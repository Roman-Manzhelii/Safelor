from pubnub_Pi.pubnub_client import PubNubClient
from mongodb.mongo_client import MongoDBClient
from datetime import datetime
import RPi.GPIO as GPIO
import threading
import asyncio
import time
import os

class WorkerComplianceHandler:
    def __init__(self):
        self.listening_channel = "roman_pi_recieve_results"
        self.requirements_channel = "zone1_get_requirements"
        self.message_container = {"response": None}
        self.response_event = threading.Event()
        self.async_response_event = asyncio.Event()
        self.requirements_updated_event = asyncio.Event()
        self.stop_zone_update = threading.Event()
        self.loop = asyncio.get_event_loop()

        self.pubnub = PubNubClient({
            self.listening_channel: self.response_handler,
            self.requirements_channel: self.requirements_response_handler
        })
    
        self.pubnub.subscribe_to_channel(self.listening_channel)
        self.pubnub.subscribe_to_channel(self.requirements_channel)

        self.mongodb = MongoDBClient()
        self.image_directory = os.path.join(os.path.dirname(__file__), "scan_images")

        self.block_unused_pins()
        self.disable_hdmi()

    def response_handler(self, message):
        self.message_container['response'] = message
        self.response_event.set()
        self.loop.call_soon_threadsafe(self.async_response_event.set)

    def requirements_response_handler(self, message):
        if "zone_requirements" in message:
            self.zone_requirements = message["zone_requirements"]
            print(f"Updated zone requirements: {self.zone_requirements}")
            self.requirements_updated_event.set()


    async def request_zone_requirements(self, zone_id):
        self.requirements_updated_event.clear()
        request_message = {"zone_id": zone_id, "listening_channel": self.requirements_channel}
        self.pubnub.publish_message("get_zone_requirements", request_message)

        try:
            await asyncio.wait_for(self.requirements_updated_event.wait(), timeout=5)
        except asyncio.TimeoutError:
            print("Failed to fetch zone requirements within timeout.")
        return self.zone_requirements

    async def upload_image_and_get_id(self, filename):
        image_path = os.path.join(self.image_directory, filename)
        return await asyncio.to_thread(self.mongodb.upload_image, image_path)

    def get_current_zone_requirements(self):
        return self.zone_requirements

    async def analyze_worker_and_ppe(self, filename, speaker, premature_exit, zone_id):
        image_id = await self.upload_image_and_get_id(filename)
        self.async_response_event.clear()
        emp_identified = False
        ppe_missing = []

        image_to_be_checked = {
            "image_id": str(image_id),
            "listening_channel": self.listening_channel,
            "zone_id": zone_id
        }

        self.pubnub.publish_message("image_for_detection", image_to_be_checked)

        start_time = time.time()
        speaker_interval = 8
        next_speaker_time = start_time + speaker_interval

        while True:
            if premature_exit.is_set():
                break

            try:
                await asyncio.wait_for(self.async_response_event.wait(), timeout=1)
                self.async_response_event.clear()
                response = self.message_container["response"]

                ppe_missing = response.get("id_ppe_not_detected", [])
                emp_identified = response.get("face_detected", False)
                ppe_missing = [ppe_id for ppe_id in ppe_missing if ppe_id != 3]
                break

            except asyncio.TimeoutError:
                pass

            current_time = time.time()
            if current_time >= next_speaker_time:
                await speaker.play_audio("image_analysis_in_progress_please_wait")
                next_speaker_time += speaker_interval

            if current_time - start_time >= speaker_interval * 4 - 1:
                break


        return set(ppe_missing), emp_identified, image_id


    def send_result(self, scan_image_id_initial, scan_image_id, emp_identified, ppe_missing, HZoneEntered, zone_requirements):
        current_time = datetime.now()

        scan_data = {
            "zone_id": 1,
            "ppe_missing": list(ppe_missing),
            "data_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "HZoneEntered": HZoneEntered.value == 1,
            "emp_identified": emp_identified,
            "scan_image_id": str(scan_image_id) if scan_image_id else str(scan_image_id_initial),
            "current_requirements": zone_requirements
        }

        self.pubnub.publish_message("scan_data_chan", scan_data)

    def start_zone_online_update(self, zone_id):
        def update_zone():
            while not self.stop_zone_update.is_set():
                try:
                    self.pubnub.publish_message("zone_online_update", {"zone_id": zone_id})
                    print(f"Zone {zone_id} online update sent.")
                except Exception as e:
                    print(f"Failed to send zone online update: {e}")
                time.sleep(60)

        threading.Thread(target=update_zone, daemon=True).start()

    def stop_zone_updates(self):
        self.stop_zone_update.set()

    def block_unused_pins(self):
        self.unused_pins = [3, 4, 5, 7, 8, 9, 10, 12, 14, 15, 16, 17, 18, 20, 26, 27, 28, 30, 32, 34, 35, 36, 37, 38, 39, 40]
        GPIO.setmode(GPIO.BOARD)
        for pin in self.unused_pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print("Unused GPIO pins blocked.")

    def unblock_pins(self):
        GPIO.cleanup()
        print("GPIO pins unblocked.")  

    def disable_hdmi(self):
        os.system("sudo tvservice -o")
        print("HDMI disabled.")

    def enable_hdmi(self):
        os.system("sudo tvservice -p")
        print("HDMI enabled.")

    def close_connections(self):
        self.pubnub.unsubscribe_to_channel(self.listening_channel)
        self.mongodb.close()
        self.unblock_pins()
        self.enable_hdmi()