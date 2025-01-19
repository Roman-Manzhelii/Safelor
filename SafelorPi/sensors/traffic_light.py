import RPi.GPIO as GPIO
import asyncio

RED_PIN = 29
YELLOW_PIN = 31
GREEN_PIN = 33

class TrafficLight:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(RED_PIN, GPIO.OUT)
        GPIO.setup(YELLOW_PIN, GPIO.OUT)
        GPIO.setup(GREEN_PIN, GPIO.OUT)

    def set_red(self):
        self.turn_off_all()
        GPIO.output(RED_PIN, GPIO.HIGH)

    def set_yellow(self):
        self.turn_off_all()
        GPIO.output(YELLOW_PIN, GPIO.HIGH)

    def set_green(self):
        self.turn_off_all()
        GPIO.output(GREEN_PIN, GPIO.HIGH)

    async def flash_colors(self):
        for _ in range(2):
            self.set_red()
            await asyncio.sleep(0.3)
            self.set_yellow()
            await asyncio.sleep(0.3)
            self.set_green()
            await asyncio.sleep(0.3)


    def turn_off_all(self):
        GPIO.output(RED_PIN, GPIO.LOW)
        GPIO.output(YELLOW_PIN, GPIO.LOW)
        GPIO.output(GREEN_PIN, GPIO.LOW)

    def cleanup(self):
        self.turn_off_all()
        GPIO.cleanup()
