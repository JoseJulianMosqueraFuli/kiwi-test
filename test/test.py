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

    # def test_create_delivery(self):
    #     authorization_token = "Bearer fake_token"
    #     with patch("firebase_admin.auth.verify_id_token") as verify_id_token_mock:
    #         verify_id_token_mock.return_value = {"uid": "fake_user_id"}
    #         payload = {
    #             "state": "pending",
    #             "pickup": {"pickup_lat": 10, "pickup_lon": 20},
    #             "dropoff": {"dropoff_lat": 30, "dropoff_lon": 40},
    #             "zone_id": "zone_1",
    #         }
    #         headers = {"Authorization": authorization_token}
    #         response = self.post("/deliveries", json=payload, headers=headers)
    #         assert response.status_code == 200

    #         assert "Delivery created with ID:" in response.get_data(as_text=True)

    # def test_get_deliveries(self, firestore):
    #     delivery_data = {
    #         "state": "pending",
    #         "pickup": {"pickup_lat": 1.0, "pickup_lon": 2.0},
    #         "dropoff": {"dropoff_lat": 3.0, "dropoff_lon": 4.0},
    #         "zone_id": "zone1",
    #     }
    #     delivery_ref = firestore.collection("deliveries").document()
    #     delivery_ref.set(delivery_data)

    #     creator_data = {"delivery_id": delivery_ref.id, "creator_id": "user1"}
    #     creator_ref = firestore.collection("deliveries_creator").document()
    #     creator_ref.set(creator_data)

    #     response = client.get(f"/deliveries?id={delivery_ref.id}")
    #     assert response.status_code == 200
    #     assert response.json == delivery_data

    #     response = client.get(f"/deliveries?creator_id={creator_data['creator_id']}")
    #     assert response.status_code == 200
    #     assert response.json == [delivery_data]

    #     response = client.get(f"/deliveries?creator_id=non_existing_user")
    #     assert response.status_code == 404
    #     assert response.json == {
    #         "message": "No deliveries found for provided creator_id."
    #     }

    #     response = client.get("/deliveries")
    #     assert response.status_code == 400
    #     assert response.json == {
    #         "message": "Please provide an id or creator_id parameter."
    #     }

    # def test_create_bot(client):
    #     # Define test data
    #     data = {
    #         "status": "available",
    #         "location": {"lat": 40.712776, "lon": -74.005974},
    #         "zone_id": "zone1",
    #     }

    #     # Make POST request to create bot
    #     response = client.post("/bots", json=data)

    #     # Verify response
    #     assert response.status_code == 201
    #     assert response.json["status"] == "available"
    #     assert response.json["location"]["lat"] == 40.712776
    #     assert response.json["location"]["lon"] == -74.005974
    #     assert response.json["zone_id"] == "zone1"

    #     # Verify bot is created in the database
    #     bot_doc = db.collection("bots").document(response.json["id"]).get()
    #     assert bot_doc.exists
    #     assert bot_doc.to_dict()["status"] == "available"
    #     assert bot_doc.to_dict()["location"]["lat"] == 40.712776
    #     assert bot_doc.to_dict()["location"]["lon"] == -74.005974
    #     assert bot_doc.to_dict()["zone_id"] == "zone1"

    # def test_get_bots(app, client):
    #     # Create a bot in the zone
    #     bot_id = str(uuid.uuid4())
    #     bot_doc = {
    #         "id": bot_id,
    #         "status": "active",
    #         "location": {"lat": 37.7749, "lon": -122.4194},
    #         "zone_id": "zone1",
    #     }
    #     db.collection("bots").document(bot_id).set(bot_doc)

    #     # Make a request to get the bots in the zone
    #     response = client.get("/bots?zone_id=zone1")
    #     assert response.status_code == 200

    #     # Check that the response contains the created bot
    #     assert len(response.json) == 1
    #     assert response.json[0]["id"] == bot_id
    #     assert response.json[0]["status"] == "active"
    #     assert response.json[0]["location"]["lat"] == 37.7749
    #     assert response.json[0]["location"]["lon"] == -122.4194

    #     # Make a request to get the bots in a non-existent zone
    #     response = client.get("/bots?zone_id=zone2")
    #     assert response.status_code == 404
    #     assert response.json["message"] == "No bots found in this zone."
