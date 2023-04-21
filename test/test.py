import json
from unittest.mock import patch, MagicMock

from flask_testing import TestCase
from flask import current_app, url_for

from main import app


class MainTest(TestCase):
    def create_app(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLES"] = False
        return app

    def test_app_exist(self):
        self.assertEqual(current_app, app)

    def test_app_in_test_mode(self):
        self.assertTrue(current_app.config["TESTING"])

    def test_index_redirect(self):
        response = self.client.get(url_for("index"))

    # @todo: all test
    def test_login_user_with_valid_credentials(self):
        with self.client:
            response = self.client.post(
                "/login_user",
                data={"email": "test@example.com", "password": "password"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            response_json = response.get_json()
            self.assertIn("idToken", response_json)

    def test_create_user_with_valid_data(self):
        with self.client:
            response = self.client.post(
                "/signup_user",
                json={
                    "email": "test@example.com",
                    "password": "password",
                    "display_name": "Test User",
                    "disabled": False,
                },
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                "Successfully created new user:", response.get_data(as_text=True)
            )

    def test_create_bot_with_valid_data(self):
        with self.client:
            response = self.client.post(
                "/bots",
                json={
                    "status": "available",
                    "location": {"lat": 37.7749, "lon": -122.4194},
                    "zone_id": "123",
                },
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 201)
            response_json = response.get_json()
            self.assertIn("id", response_json)
            self.assertEqual(response_json["status"], "available")
            self.assertEqual(response_json["location"]["lat"], 37.7749)
            self.assertEqual(response_json["location"]["lon"], -122.4194)
            self.assertEqual(response_json["zone_id"], "123")
