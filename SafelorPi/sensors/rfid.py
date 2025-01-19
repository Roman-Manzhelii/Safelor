from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
import asyncio

class RFIDScanner:
    def __init__(self):
        self.reader = SimpleMFRC522()
        self.cleaned = False

    async def scan(self):
        if self.cleaned:
            print("RFID: Scanner is cleaned and inactive.")
            return False

        print("RFID: Scanning for tag.")
        start_time = time.time()
        while time.time() - start_time < 3:
            try:
                _, text = await asyncio.to_thread(self.reader.read_no_block)
                if text:
                    print(f"RFID: Tag detected! Text: {text}")
                    return True
            except Exception as e:
                print(f"RFID: Error during scan - {e}")
                return False
            await asyncio.sleep(0.1)
        print("RFID: No tag detected within 3 seconds.")
        return False
    
    def reset(self):
        if self.cleaned:
            self.reader = SimpleMFRC522()
            self.cleaned = False
            print("RFID: Scanner reactivated and ready.")

    def cleanup(self):
        if not self.cleaned:
            self.cleaned = True
            print("RFID: Memory cleaned up, scanner deactivated.")
        else:
            print("RFID: Already cleaned.")
