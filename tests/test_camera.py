import unittest
from unittest.mock import MagicMock
import sys
sys.modules['picamera2'] = MagicMock()
from SafelorPi.mock_sensors.mock_camera import MockCamera
from SafelorPi.sensors.camera import Camera
class TestCamera(unittest.TestCase):
    def setUp(self):
        self.camera = MockCamera()

    def tearDown(self):
        del self.camera

    def test_camera_initialization(self):
        # Simulate Camera initialization
        self.assertIsNotNone(self.camera)
        print("Mock Camera initialized successfully.")

    def test_capture_image(self):
        # Test capturing an image
        filename = self.camera.capture_image()
        self.assertFalse(filename.endswith("test_image.jpg"))
        print(f"Captured image: {filename}")

    def test_check_image_for_ppe(self):
        # Test PPE detection
        ppe_missing = self.camera.check_image_for_ppe("test_image.jpg")
        self.assertIn("hi-vis", ppe_missing)
        print(f"Detected missing PPE: {ppe_missing}")

    def test_check_image_for_face(self):
        # Test face detection
        face_detected = self.camera.check_image_for_face("test_image.jpg")
        self.assertTrue(face_detected)
        print("Face detected successfully.")

    def test_perform_ppe_check(self):
        # Test full PPE check
        emp_id, emp_identified, ppe_missing = self.camera.perform_ppe_check("test_image.jpg")
        self.assertEqual(emp_id, "12345")
        self.assertTrue(emp_identified)
        self.assertIn("hi-vis", ppe_missing)
        print(f"PPE check results: emp_id={emp_id}, emp_identified={emp_identified}, ppe_missing={ppe_missing}")


if __name__ == "__main__":
    unittest.main()
