import unittest
from SafelorPi.sensors.speaker import Speaker
from SafelorPi.mock_sensors.mock_speaker import MockSpeaker


class TestSpeaker(unittest.TestCase):
    def setUp(self):
        self.speaker = Speaker()
    #Main Sensor
    # def test_say_message(self):
    #     message = "Testing Speaker"
    #     self.speaker.say(message)
    #     self.assertIn(message, self.speaker.messages)  # Verify message recording
    #     print("Test: Speaker message recorded successfully")

    def test_say_message(self):
        message = "Testing Speaker"
        self.speaker.say(message)
        self.assertIn(message, self.speaker.messages)  # MockSpeaker stores messages
        print("Test: Speaker message recorded successfully")

if __name__ == "__main__":
    unittest.main()
