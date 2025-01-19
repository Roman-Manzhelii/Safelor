try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from unittest.mock import MagicMock
    GPIO = MagicMock()

import time
import asyncio
from multiprocessing import Value

class PIRSensor:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN)

    def is_triggered(self):
        return GPIO.input(self.pin)

    def cleanup(self):
        GPIO.cleanup()

def monitor_pir(pir1, pir2, HZoneEntered, premature_exit, stop_monitoring):
    pir_triggered_once = False
    time.sleep(3)
    while not stop_monitoring.is_set():
        if not pir_triggered_once and pir1.is_triggered():
            HZoneEntered.value = 0
            premature_exit.set()
            pir_triggered_once = True
            print("Premature exit, HZoneEntered = False")
        elif not pir_triggered_once and pir2.is_triggered():
            HZoneEntered.value = 1
            premature_exit.set()
            pir_triggered_once = True
            print("Premature exit, HZoneEntered = True")

        if pir_triggered_once and not pir1.is_triggered() and not pir2.is_triggered():
            pir_triggered_once = False

        time.sleep(0.1)

async def wait_for_entry_and_exit(pir1, pir2, speaker, HZoneEntered):
    HZoneEntered.value = -1

    pir2_triggered = False
    pir1_triggered = False

    while not pir2_triggered and not pir1_triggered:
        start_time = time.time()

        while not pir2_triggered and not pir1_triggered and time.time() - start_time < 5:
            pir2_triggered = pir2.is_triggered()
            pir1_triggered = pir1.is_triggered()
            await asyncio.sleep(0.1)

        if not pir2_triggered and not pir1_triggered:
            asyncio.create_task(speaker.play_audio("please_proceed"))

    await asyncio.sleep(0.1)

    if pir2_triggered:
        HZoneEntered.value = 1
        await speaker.play_audio("entering_hazard_zone")
    elif pir1_triggered:
        HZoneEntered.value = 0
        await speaker.play_audio("exiting_hazard_zone")
