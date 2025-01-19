class MockRFIDScanner:
    def __init__(self):
        self.tag_detected = False

    def scan(self):
        print("Mock RFID: Scanning...")
        return self.tag_detected

    def simulate_tag(self, detected=True):
        self.tag_detected = detected
