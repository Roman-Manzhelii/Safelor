import unittest
from SafelorPi.sensors.rfid import RFIDScanner
from SafelorPi.mock_sensors.mock_rfid import MockRFIDScanner


class TestRFIDScanner(unittest.TestCase):
    def setUp(self):
        self.rfid_scanner = MockRFIDScanner()

    def test_scan_no_tag(self):
        self.rfid_scanner.simulate_tag(detected=False)
        tag_detected = self.rfid_scanner.scan()
        self.assertFalse(tag_detected)
        print("Test: No RFID tag detected")

    def test_scan_with_tag(self):
        self.rfid_scanner.simulate_tag(detected=True)
        tag_detected = self.rfid_scanner.scan()
        self.assertTrue(tag_detected)
        print("Test: RFID tag detected")


if __name__ == "__main__":
    unittest.main()
