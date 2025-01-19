import unittest
from unittest.mock import MagicMock
from SafelorApp.pubnub.handlers import Channel_Handler
from SafelorApp.mongodb.mongo_client import MongoDBClient

class TestChannelHandler(unittest.TestCase):

    def setUp(self):
        self.mongodb = MongoDBClient()
        self.channel_handler = Channel_Handler(self.mongodb)
        self.channel_handler.pubnub_client = MagicMock()

    def test_handle_scan_data_channel(self):
        data = {"HZoneEntered": True, "ppe_missing": [1, 2]}
        self.mongodb.upload_scan = MagicMock(return_value="mock_id")
        self.channel_handler.handle_scan_data_channel(data)
        self.channel_handler.pubnub_client.publish_message.assert_called_with(
            "ppe_violation", {"scan_id": "mock_id"}
        )

    def test_handle_get_zone_requirements(self):
        data = {"zone_id": 1, "listening_channel": "test_channel"}
        self.mongodb.get_zone_by_id = MagicMock(return_value={"ppe_required": [1, 2]})
        self.channel_handler.handle_get_zone_requirements(data)
        self.channel_handler.pubnub_client.publish_message.assert_called_with(
            "test_channel", {"zone_requirements": [1, 2]}
        )

if __name__ == '__main__':
    unittest.main()