import unittest
from unittest.mock import patch, MagicMock
from SafelorApp.mongodb.mongo_client import MongoDBClient

class TestMongoDB(unittest.TestCase):

    @patch("SafelorApp.mongodb.mongo_client.MongoClient")
    def test_get_users(self, mock_mongo):
        mock_client_instance = mock_mongo.return_value
        mock_client_instance.user_collection.find.return_value = [{"user_id": 1}]
        
        mongodb = MongoDBClient()
        users = mongodb.get_users()
        self.assertEqual(len(users), 1)

if __name__ == "__main__":
    unittest.main()
