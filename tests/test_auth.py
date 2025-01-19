import unittest
from unittest.mock import patch
from SafelorApp.app import app  # Importing Flask app for testing

class TestAuth(unittest.TestCase):
    
    def setUp(self):
        self.client = app.test_client()

    @patch("SafelorApp.mongodb.mongo_client.MongoDBClient.get_user_by_email")
    def test_login_with_valid_credentials(self, mock_get_user):
        # Mocking user retrieval from MongoDB
        mock_get_user.return_value = {
            "google_id": "12345",
            "name": "Test User",
            "email": "testuser@example.com",
            "access_level": "admin"
        }
        
        # Simulate login request
        response = self.client.get("/google_login")
        self.assertEqual(response.status_code, 302)  # Expecting redirect to auth page
    
    def test_unauthorized_access(self):
        response = self.client.get("/zones", follow_redirects=True)
        self.assertIn(b"Login to Safelor", response.data)  # Expecting to be redirected to login

if __name__ == "__main__":
    unittest.main()
