from SafelorPi.mock_sensors.mock_camera import MockCamera
from SafelorPi.mock_sensors.mock_pir import MockPIRSensor
from SafelorPi.mock_sensors.mock_rfid import MockRFIDScanner
from SafelorPi.mock_sensors.mock_traffic import MockTrafficLight
from SafelorPi.mock_sensors.mock_speaker import MockSpeaker

def test_mock_camera():
    camera = MockCamera()
    image_path = camera.capture_image()
    assert image_path.endswith("test_image.jpg"), "MockCamera: Failed to return the test image."

def test_mock_pir_sensor():
    pir = MockPIRSensor(pin=11)
    assert not pir.is_triggered(), "MockPIRSensor: Should not detect motion initially."
    pir.simulate_motion()
    assert pir.is_triggered(), "MockPIRSensor: Should detect motion after simulation."

def test_mock_rfid_scanner():
    rfid = MockRFIDScanner()
    assert not rfid.scan(), "MockRFIDScanner: Should not detect a tag initially."
    rfid.simulate_tag()
    assert rfid.scan(), "MockRFIDScanner: Should detect a tag after simulation."

def test_mock_traffic_light():
    traffic_light = MockTrafficLight()
    traffic_light.set_red()
    assert traffic_light.state == "RED", "MockTrafficLight: Failed to set red state."
    traffic_light.set_green()
    assert traffic_light.state == "GREEN", "MockTrafficLight: Failed to set green state."
    traffic_light.turn_off_all()
    assert traffic_light.state == "OFF", "MockTrafficLight: Failed to turn off all lights."

def test_mock_speaker():
    speaker = MockSpeaker()
    test_message = "Test message for MockSpeaker"
    speaker.say(test_message)
    assert test_message in speaker.messages, "MockSpeaker: Failed to store the spoken message."


if __name__ == "__main__":
    print("Running tests for mock sensors...")

    test_mock_camera()
    test_mock_pir_sensor()
    test_mock_rfid_scanner()
    test_mock_traffic_light()
    test_mock_speaker()
    
    print("All tests for mock sensors passed successfully!")
 