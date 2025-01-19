from pubnub.pnconfiguration import PNConfiguration
from pubnub.models.consumer.v3.channel import Channel
from pubnub.pubnub import PubNub, SubscribeCallback
from pubnub.exceptions import PubNubException
from SafelorApp.pubnub.listeners import PubNubListener
import os
from dotenv import load_dotenv


class PubNubClient:
    def __init__(self, handlers = {},cipher=None):
        load_dotenv()
        self.pubnub = None
        self.cipher = cipher
        self.handlers = handlers
        self.initiate_pubnub()


    def initiate_pubnub(self):
        try:
            print("Cipher key in pubnub config ",self.cipher)
            pnconfig = PNConfiguration()
            pnconfig.publish_key = os.getenv("PUBLISH_PUBNUB_KEY")
            pnconfig.subscribe_key = os.getenv("SUBSCRIBE_PUBNUB_KEY")
            pnconfig.secret_key = os.getenv("SECRET_PUBNUB_KEY")
            pnconfig.ssl = True
            pnconfig.cipher_key = self.cipher
            pnconfig.uuid = os.getenv("PUBNUB_USERID")
            self.pubnub = PubNub(pnconfig)
            self.pubnub.add_listener(PubNubListener(self.handlers))
            print("PubNub connected successfully")
        except Exception as e:
            print(f"PubNub connection failed: {e}")
    
    
    def publish_message(self, channel, message):
        try:
            print(f"Publish message on {channel}. Message : {message}")
            envelope = self.pubnub.publish().channel(channel).message(message).sync()
            if envelope.status.is_error():
                print(f"Error publishing message on {channel}")
            else:
                print("Message published")
        except PubNubException as e:
            print("Error publishing:", e)
            return True


    def subscribe_to_channel(self, channel):
        # Subscribe to a specified channel
        self.pubnub.subscribe().channels(channel).execute()
        
        
    def generate_token_client(self):
        try:
            channels = [
            Channel.id("ppe_violation").read(),
            Channel.id("change_zone_requirements").write(),
            Channel.id("get_unchecked_scans").write(),
            Channel.id("recieve_unchecked_scans").read(),
            Channel.id("get_online_status").write(),
            Channel.id("return_online_status").read(),
            ]
            envelope = self.pubnub.grant_token().channels(channels).ttl(20).sync()
            return envelope.result.token
        except Exception as e:
            print(f"Token generation failed: {e}")
            return True
        

    def generate_token_pi(self):
        try:
            channels = [
            Channel.id("ppe_violation").read().write(),
            Channel.id("roman_pi_recieve_results").read(),
            Channel.id("image_for_detection").write(),
            Channel.id("zone_online_update").write(),
            Channel.id("scan_data_chan").write(),
            Channel.id("zone1_get_requirements").read(),
            Channel.id("get_zone_requirements").write()
            ]
            envelope = self.pubnub.grant_token().channels(channels).ttl(20).sync()
            return envelope.result.token
        except Exception as e:
            print(f"Token generation failed: {e}")
            return True
        
        
