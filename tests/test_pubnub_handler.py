import time
from unittest.mock import patch, MagicMock
import pytest
from SafelorPi.pubnub_Pi.pubnub_client import PubNubClient
from SafelorPi.pubnub_Pi.listeners import PubNubListener
from tests.utils.mock_env import mock_pubnub_env 

@pytest.fixture
def mock_pubnub_client(mock_pubnub_env):
    with patch("SafelorPi.pubnub_Pi.pubnub_client.PubNub") as MockPubNub:
        instance = MockPubNub.return_value

        # Mock the publish method chain: publish().channel().message().sync().status.is_error
        publish_mock = MagicMock()
        channel_mock = MagicMock()
        message_mock = MagicMock()
        sync_mock = MagicMock()

        # Correctly set `sync().status.is_error` to a boolean value
        sync_mock.status.is_error = False
        message_mock.sync.return_value = sync_mock
        channel_mock.message.return_value = message_mock
        publish_mock.channel.return_value = channel_mock
        instance.publish.return_value = publish_mock

        instance.subscribe.return_value.execute.return_value = None
        instance.add_listener.return_value = None

        client = PubNubClient()
        yield client, instance


def test_pubnub_publish_message(mock_pubnub_client):
    pubnub_client, pubnub_instance = mock_pubnub_client

    channel = "test_channel"
    message = {"key": "value"}
    error = pubnub_client.publish_message(channel, message)

    # Debugging statements
    print(f"Mock publish call args: {pubnub_instance.publish.call_args_list}")
    print(f"Mock publish.sync return: {pubnub_instance.publish().channel().message().sync.return_value}")
    print(f"Mock status.is_error: {pubnub_instance.publish().channel().message().sync().status.is_error}")

    # Assertions
    pubnub_instance.publish.assert_called_once()  
    pubnub_instance.publish().channel.assert_called_once_with(channel)  
    pubnub_instance.publish().channel().message.assert_called_once_with(message)  
    pubnub_instance.publish().channel().message().sync.assert_called_once() 
    assert not error, "Message publishing failed"
    print(f"Message published to channel '{channel}': {message}")



def test_pubnub_subscription(mock_pubnub_client):
    pubnub_client, pubnub_instance = mock_pubnub_client

    # Mock listener
    received_messages = []
    def handle_message(data):
        received_messages.append(data)

    listener = PubNubListener(handlers={"test_channel": handle_message})
    pubnub_client.pubnub.add_listener(listener)

    # Simulate message reception
    test_message = {"key": "test_subscription"}
    listener.message(pubnub_client.pubnub, MagicMock(channel="test_channel", message=test_message))

    # Assertions
    assert received_messages, "No message received"
    assert received_messages[0] == test_message, "Message content mismatch"
    print(f"Message received: {received_messages[0]}")


def test_pubnub_handler_logic(mock_pubnub_client):
    pubnub_client, pubnub_instance = mock_pubnub_client

    # Simulate a PubNub listener with a handler
    received_messages = []
    def handle_test_channel(data):
        received_messages.append(data)

    listener = PubNubListener(handlers={"test_channel": handle_test_channel})
    pubnub_client.pubnub.add_listener(listener)

    # Simulate message reception
    test_message = {"key": "test_handler"}
    listener.message(pubnub_client.pubnub, MagicMock(channel="test_channel", message=test_message))

    # Assertions
    assert received_messages, "Handler was not triggered"
    assert received_messages[0] == test_message, "Handler received incorrect data"
    print(f"Handler processed message: {received_messages[0]}")
