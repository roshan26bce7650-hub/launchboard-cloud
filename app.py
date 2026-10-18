import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "launchboard.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-production")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            color TEXT DEFAULT '#6d5dfc',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Todo',
            priority TEXT NOT NULL DEFAULT 'Medium',
            due_date TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.before_request
def ensure_database():
    if not os.path.exists(DATABASE):
        init_db()


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password with at least 8 characters.", "error")
            return render_template("register.html")
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password))
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "error")
            return render_template("register.html")
        user = db.execute("SELECT id, name FROM users WHERE email = ?", (email,)).fetchone()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    uid = session["user_id"]
    projects = db.execute("""
        SELECT p.*, COUNT(t.id) AS task_count,
               SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) AS done_count
        FROM projects p LEFT JOIN tasks t ON t.project_id = p.id
        WHERE p.user_id = ?
        GROUP BY p.id ORDER BY p.created_at DESC
    """, (uid,)).fetchall()
    totals = db.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) AS done,
               SUM(CASE WHEN status != 'Done' THEN 1 ELSE 0 END) AS open
        FROM tasks WHERE user_id = ?
    """, (uid,)).fetchone()
    recent_tasks = db.execute("""
        SELECT t.*, p.name AS project_name, p.color AS project_color
        FROM tasks t JOIN projects p ON p.id = t.project_id
        WHERE t.user_id = ? ORDER BY
        CASE t.status WHEN 'In progress' THEN 0 WHEN 'Todo' THEN 1 ELSE 2 END,
        t.created_at DESC LIMIT 6
    """, (uid,)).fetchall()
    return render_template("dashboard.html", projects=projects, totals=totals, recent_tasks=recent_tasks)


@app.route("/projects", methods=["POST"])
@login_required
def create_project():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    color = request.form.get("color", "#6d5dfc")
    if name:
        get_db().execute(
            "INSERT INTO projects (user_id, name, description, color) VALUES (?, ?, ?, ?)",
            (session["user_id"], name, description, color)
        )
        get_db().commit()
        flash("Project created successfully.", "success")
    else:
        flash("Project name is required.", "error")
    return redirect(url_for("dashboard"))


@app.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    db = get_db()
    project = db.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("dashboard"))
    tasks = db.execute(
        "SELECT * FROM tasks WHERE project_id = ? AND user_id = ? ORDER BY created_at DESC",
        (project_id, session["user_id"])
    ).fetchall()
    return render_template("project.html", project=project, tasks=tasks)


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    db = get_db()
    db.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, session["user_id"]))
    db.commit()
    flash("Project deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/projects/<int:project_id>/tasks", methods=["POST"])
@login_required
def create_task(project_id):
    db = get_db()
    project = db.execute(
        "SELECT id FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()
    title = request.form.get("title", "").strip()
    status = request.form.get("status", "Todo")
    priority = request.form.get("priority", "Medium")
    due_date = request.form.get("due_date", "").strip()
    if not project:
        flash("Project not found.", "error")
    elif title:
        if status not in ["Todo", "In progress", "Done"]:
            status = "Todo"
        if priority not in ["Low", "Medium", "High"]:
            priority = "Medium"
        db.execute(
            "INSERT INTO tasks (project_id, user_id, title, status, priority, due_date) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, session["user_id"], title, status, priority, due_date)
        )
        db.commit()
        flash("Task added.", "success")
    else:
        flash("Task title is required.", "error")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_task_status(task_id):
    status = request.form.get("status", "Todo")
    if status not in ["Todo", "In progress", "Done"]:
        status = "Todo"
    db = get_db()
    task = db.execute(
        "SELECT id, project_id FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    ).fetchone()
    if task:
        db.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        db.commit()
        return redirect(url_for("project_detail", project_id=task["project_id"]))
    flash("Task not found.", "error")
    return redirect(url_for("dashboard"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    db = get_db()
    task = db.execute(
        "SELECT id, project_id FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    ).fetchone()
    if task:
        project_id = task["project_id"]
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        flash("Task deleted.", "success")
        return redirect(url_for("project_detail", project_id=project_id))
    flash("Task not found.", "error")
    return redirect(url_for("dashboard"))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
