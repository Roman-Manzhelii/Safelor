class MockPIRSensor:
    def __init__(self, pin):
        self.pin = pin
        self.motion_detected = False

    def is_triggered(self):
        return self.motion_detected

    def simulate_motion(self):
        self.motion_detected = True

    def cleanup(self):
        print("MockPIRSensor: Clean up called.")
