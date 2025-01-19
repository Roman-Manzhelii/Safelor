class MockSpeaker:
    def __init__(self):
        self.messages = []

    def say(self, message):
        print(f"Mock Speaker: {message}")
        self.messages.append(message)