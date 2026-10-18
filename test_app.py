import os
import tempfile
import unittest
import app as launchboard


class LaunchboardTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        launchboard.DATABASE = self.db_path
        launchboard.app.config["TESTING"] = True
        launchboard.app.config["SECRET_KEY"] = "test-secret"
        launchboard.init_db()
        self.client = launchboard.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_landing_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Big ideas deserve", response.data)

    def test_register_and_dashboard(self):
        response = self.client.post("/register", data={
            "name": "Test User", "email": "test@example.com", "password": "password123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your workspace", response.data)

    def test_health(self):
        self.assertEqual(self.client.get("/health").json["status"], "ok")


if __name__ == "__main__":
    unittest.main()
