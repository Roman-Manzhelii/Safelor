import unittest
from unittest.mock import patch
from SafelorApp.mongodb.mongo_client import MongoDBClient
from SafelorApp.pubnub.pubnub_client import PubNubClient
from pubnub.callbacks import SubscribeCallback
import time
import os
from datetime import datetime


class MongoDBTests(unittest.TestCase):
    def setUp(self):
        self.client = MongoDBClient()

    def test_mongo_connection(self):
        """Test MongoDB connection"""
        self.assertIsNotNone(self.client.db, "Failed to connect to MongoDB")

    def test_insert_user(self):
        """Test inserting a valid user into MongoDB"""
        user_data = {"name": "John Doe", "role": "worker", "email": "johndoe@example.com"}
        user_id = self.client.insert_user(user_data)
        self.assertIsNotNone(user_id, "Failed to insert user")
        print(f"Inserted user ID: {user_id}")

    def test_get_users(self):
        """Test retrieving all users from MongoDB"""
        users = self.client.get_users()
        self.assertIsInstance(users, list, "Expected a list of users")
        print(f"Retrieved users: {users}")

    def test_image_upload(self):
        """Test uploading an image to GridFS"""
        image_path = "/Users/aondo/Safelor/SafelorPi/scan_images/test_image.jpg"
        image_id = self.client.upload_image(image_path)
        self.assertIsNotNone(image_id, "Image upload failed")
        print(f"Uploaded image ID: {image_id}")

    def test_scan_data_upload(self):
        """Test uploading scan data"""
        scan_data = {
            "emp_id": 1001,
            "zone_id": 1,
            "ppe_missing": [3],
            "date_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "HZoneEntered": True,
            "emp_identified": True
        }
        scan_id = self.client.upload_scan(scan_data)
        self.assertIsNotNone(scan_id, "Scan data upload failed")
        print(f"Uploaded scan ID: {scan_id}")

    def test_invalid_user_insertion(self):
        """Test inserting invalid user data into MongoDB"""
        invalid_user_data = {"name": None, "role": "worker", "email": None}
        user_id = self.client.insert_user(invalid_user_data)
        self.assertIsNone(user_id, "Invalid user insertion should fail")
        print("Invalid user insertion test passed.")

    def test_invalid_image_path(self):
        """Test uploading an image with an invalid path"""
        invalid_image_path = "../../SafelorPi/scan_images/non_existent_image.jpg"
        image_id = self.client.upload_image(invalid_image_path)
        self.assertIsNone(image_id, "Image upload with invalid path should fail")
        print("Invalid image path test passed.")


class PubNubTests(unittest.TestCase):
    def setUp(self):
        self.client = PubNubClient()

    def test_pubnub_configuration(self):
        """Test PubNub configuration"""
        self.assertIsNotNone(self.client.pubnub, "Failed to initialize PubNub client")
        print("PubNub configuration test passed.")

    def test_publish_message(self):
        """Test publishing a message to a PubNub channel"""
        result = self.client.publish_message("test_channel", "Hello, PubNub!")
        self.assertFalse(result, "Failed to publish message")
        print("Message published successfully.")

    def test_subscribe_to_channel(self):
        """Test subscribing to a PubNub channel and receiving a message"""
        class TestListener(SubscribeCallback):
            def message(self, pubnub, message):
                self.assertEqual(message.message, "Hello, PubNub!", "Received incorrect message content")
                print(f"Received message: {message.message}")

        listener = TestListener()
        self.client.pubnub.add_listener(listener)
        self.client.subscribe_to_channel("test_channel")
        self.client.publish_message("test_channel", "Hello, PubNub!")
        time.sleep(1)  # Wait for message to be received

    @patch.dict(os.environ, {"PUBLISH_PUBNUB_KEY": "invalid", "SUBSCRIBE_PUBNUB_KEY": "invalid"})
    def test_invalid_pubnub_keys(self):
        """Test PubNub initialization with invalid keys"""
        client = PubNubClient()
        self.assertIsNone(client.pubnub, "Invalid PubNub keys should prevent configuration")
        print("Invalid PubNub keys test passed.")


if __name__ == "__main__":
    unittest.main()
