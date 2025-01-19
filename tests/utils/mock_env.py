import time
from unittest.mock import patch, MagicMock
import pytest
from SafelorPi.pubnub_Pi.pubnub_client import PubNubClient
from SafelorPi.pubnub_Pi.listeners import PubNubListener

@pytest.fixture
def mock_pubnub_env(monkeypatch):
    # Mock PubNub environment variables
    monkeypatch.setenv("PUBLISH_PUBNUB_KEY", "pub-c-d084304e-e224-4c35-9531-432761626aa1")
    monkeypatch.setenv("SUBSCRIBE_PUBNUB_KEY", "sub-c-addb02ed-900a-48f7-9825-f3f66fc48dab")
    monkeypatch.setenv("SECRET_PUBNUB_KEY", "sec-c-OGJiMDEwM2UtNDIzYi00MDAwLTg3N2QtYjA3ZDgxOTczYWUx")
    monkeypatch.setenv("PUBNUB_USERID", "seanm_safelor_app")

    # Mock API responses for token and cipher key
    monkeypatch.setattr(
        "SafelorPi.pubnub_Pi.pubnub_client.PubNubClient.request_cipher_key",
        lambda self: "mock_cipher_key",
    )
    monkeypatch.setattr(
        "SafelorPi.pubnub_Pi.pubnub_client.PubNubClient.request_auth_token",
        lambda self: "mock_auth_token",
    )

@pytest.fixture
def mock_pubnub_client(mock_pubnub_env):
    # Mock the PubNub class
    with patch("SafelorPi.pubnub_Pi.pubnub_client.PubNub") as MockPubNub:
        instance = MockPubNub.return_value
        instance.publish.return_value.sync.return_value.status.is_error = False
        instance.subscribe.return_value.execute.return_value = None
        instance.add_listener.return_value = None

        client = PubNubClient()
        yield client, instance

def test_pubnub_publish_message(mock_pubnub_client):
    pubnub_client, pubnub_instance = mock_pubnub_client

    channel = "test_channel"
    message = {"key": "value"}
    error = pubnub_client.publish_message(channel, message)

    # Assertions
    pubnub_instance.publish.assert_called_once()
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

    # Simulate message publishing
    test_message = {"key": "test_subscription"}
    pubnub_client.subscribe_to_channel("test_channel")
    pubnub_client.publish_message("test_channel", test_message)

    # Wait for processing
    time.sleep(1)

    # Assertions
    pubnub_instance.subscribe.assert_called_once()
    assert received_messages, "No message received"
    print(f"Message received: {received_messages[0]}")

def test_pubnub_handler_logic(mock_pubnub_client):
    pubnub_client, pubnub_instance = mock_pubnub_client

    # Simulate a PubNub listener with a handler
    received_messages = []
    def handle_test_channel(data):
        received_messages.append(data)

    listener = PubNubListener(handlers={"test_channel": handle_test_channel})
    pubnub_client.pubnub.add_listener(listener)

    # Simulate message publishing
    test_message = {"key": "test_handler"}
    pubnub_client.subscribe_to_channel("test_channel")
    pubnub_client.publish_message("test_channel", test_message)

    # Wait for processing
    time.sleep(1)

    # Assertions
    pubnub_instance.subscribe.assert_called_once()
    assert received_messages, "Handler was not triggered"
    assert received_messages[0] == test_message, "Handler received incorrect data"
    print(f"Handler processed message: {received_messages[0]}")
