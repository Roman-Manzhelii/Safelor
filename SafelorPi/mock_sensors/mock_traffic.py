import os
class MockTrafficLight:
    def __init__(self):
        self.state = "OFF"

    def set_red(self):
        self.state = "RED"
        print("Mock Traffic Light: Red")

    def set_yellow(self):
        self.state = "YELLOW"
        print("Mock Traffic Light: Yellow")

    def set_green(self):
        self.state = "GREEN"
        print("Mock Traffic Light: Green")

    def turn_off_all(self):
        self.state = "OFF"
        print("Mock Traffic Light: All lights off")
        
    def cleanup(self):
        print("Mock TrafficLight: Cleanup called")