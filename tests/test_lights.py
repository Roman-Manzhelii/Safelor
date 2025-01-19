import unittest
from unittest.mock import patch, MagicMock
from SafelorPi.sensors.traffic_light import TrafficLight
from SafelorPi.mock_sensors.mock_traffic import MockTrafficLight


class TestTrafficLight(unittest.TestCase):
    def setUp(self):
        self.traffic_light = TrafficLight()

    def tearDown(self):
        self.traffic_light.cleanup()

    def test_set_red(self):
        self.traffic_light.set_red()
        self.assertEqual(self.traffic_light.state, "RED")
        print("Test: Traffic Light set to RED")

    def test_set_yellow(self):
        self.traffic_light.set_yellow()
        self.assertEqual(self.traffic_light.state, "YELLOW")
        print("Test: Traffic Light set to YELLOW")

    def test_set_green(self):
        self.traffic_light.set_green()
        self.assertEqual(self.traffic_light.state, "GREEN")
        print("Test: Traffic Light set to GREEN")

    def test_turn_off_all(self):
        self.traffic_light.turn_off_all()
        self.assertEqual(self.traffic_light.state, "OFF")
        print("Test: Traffic Light turned OFF")


if __name__ == "__main__":
    unittest.main()
