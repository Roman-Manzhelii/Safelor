import threading
import time
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from SafelorPi.pubnub_Pi.listeners import PubNubListener
import os, requests
from dotenv import load_dotenv

load_dotenv()
SECRET_API_KEY=os.getenv('SECRET_API_KEY')

CIPHER_SERVER_URL='http://127.0.0.1:5000/get_cipher_key'
PUBNUB_TOKEN_URL='http://127.0.0.1:5000/get_pubnub_token'

class PubNubClient:
    def __init__(self, handlers = {}):
        self.pubnub = None
        self.handlers = handlers
        self.initiate_pubnub()
        

    def initiate_pubnub(self):
        try:
            pnconfig = PNConfiguration()
            pnconfig.publish_key = os.getenv("PUBLISH_PUBNUB_KEY")
            pnconfig.subscribe_key = os.getenv("SUBSCRIBE_PUBNUB_KEY")
            pnconfig.ssl = True
            token = self.request_auth_token()
            pnconfig.auth_key = token
            pnconfig.cipher_key = self.request_cipher_key()
            pnconfig.uuid = os.getenv("PUBNUB_USERID")
            self.pubnub = PubNub(pnconfig)
            self.pubnub.add_listener(PubNubListener(self.handlers))
            refresh_thread = threading.Thread(target=self.initiate_token_refresh, args=(token,), daemon=True)
            refresh_thread.start()
            print("PubNub connected successfully")
        except Exception as e:
            print(f"PubNub connection failed: {e}")
    
    
    def publish_message(self, channel, message):
        try:
            envelope = self.pubnub.publish().channel(channel).message(message).sync()
            if envelope.status.is_error():
                print(f"Error publishing message on {channel}")
                return True
            return False
        except PubNubException as e:
            print("Error publishing:", e)
            return True


    def subscribe_to_channel(self, channel):
        # Subscribe to a specified channel
        self.pubnub.subscribe().channels(channel).execute()
        
    def unsubscribe_to_channel(self, channel):
        self.pubnub.unsubscribe().channels(channel).execute()
        
    def request_cipher_key(self):
        headers = {
            "Authorization": SECRET_API_KEY
        }
        try:
            response = requests.post(CIPHER_SERVER_URL, headers=headers)
            data = response.json()
            if "cipher_key" in data:
                print("CIPHER RECIEVED ", data["cipher_key"])
                return data["cipher_key"]
            else:
                print("Failed to retrieve cipher key")
                return None
        except Exception as e:
            print(f"Error fetching cipher key: {e}")
            return None
        
    def request_auth_token(self):
        headers = {
            "Authorization": SECRET_API_KEY
        }
        try:
            response = requests.post(PUBNUB_TOKEN_URL, headers=headers)
            data = response.json()
            if "token" in data:
                print("TOKEN RECIEVED ", data["token"])
                return data["token"]
            else:
                print("Failed to retrieve pubnub token")
                return None
        except Exception as e:
            print(f"Error fetching pubnub token: {e}")
            return None
        

    def initiate_token_refresh(self,token):
        while True:
            parsed_token = self.pubnub.parse_token(token)
            ttl_minutes = int(parsed_token.get('ttl'))
            print("Parsed token TTL ->", ttl_minutes)
            sleep_time = (ttl_minutes * 60) - 30
            time.sleep(sleep_time)
            print("Setting new token")
            token = self.request_auth_token()
            self.pubnub.set_token(token)
            #test the token

                
        
        