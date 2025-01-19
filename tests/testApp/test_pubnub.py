import unittest
from unittest.mock import patch
from SafelorApp.pubnub.pubnub_client import PubNubClient

class TestPubNub(unittest.TestCase):

    @patch("SafelorApp.pubnub.pubnub_client.PubNub")
    def test_publish_message(self, mock_pubnub):
        client = PubNubClient()
        mock_channel = "test_channel"
        mock_message = {"msg": "Hello"}

        # Publish message and verify
        result = client.publish_message(mock_channel, mock_message)
        self.assertFalse(result) 

if __name__ == "__main__":
    unittest.main()
