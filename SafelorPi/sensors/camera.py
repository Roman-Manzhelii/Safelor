import asyncio
from picamera2 import Picamera2
from datetime import datetime
import os
class Camera:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration({"size": (1920, 1080)})
        self.picam2.configure(config)
        self.save_path = os.path.join(os.path.dirname(__file__), "../scan_images")
        os.makedirs(self.save_path, exist_ok=True)
        self.picam2.start()
        print("Camera: Started")

    def __del__(self):
        self.picam2.stop()
        print("Camera: Stopped")

    async def capture_image(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_image_{timestamp}.jpg"
        full_path = os.path.join(self.save_path, filename)
        await asyncio.to_thread(self.picam2.capture_file, full_path)
        print(f"Camera: Captured image saved as {filename}")
        return filename