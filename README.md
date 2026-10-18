# Launchboard Cloud 🚀

Launchboard Cloud is a lightweight project and task dashboard built with Flask, SQLite, HTML, CSS, and JavaScript.

## Features
- User registration and login
- Personal project dashboard
- Create and delete projects
- Add tasks with status, priority, and due date
- Update task status and delete tasks
- Dashboard statistics and recent tasks
- Responsive layout
- Health-check endpoint at `/health`

## Run locally
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   python app.py
   ```
5. Open `http://127.0.0.1:5000`.

The SQLite database is created automatically when the app starts.

## Deploy to Render
This repository includes `render.yaml`. Push the project to GitHub and create a new Web Service on Render from the repository. Render can use the included configuration. Set a strong `SECRET_KEY` in the service environment if you manage environment variables manually.

**Note:** SQLite data stored on a typical ephemeral Render filesystem may not persist across redeploys. For production use, connect a managed PostgreSQL database and add CSRF protection, rate limiting, and email verification.

## Built with
- Python / Flask
- SQLite
- HTML5 / CSS3
- Vanilla JavaScript
