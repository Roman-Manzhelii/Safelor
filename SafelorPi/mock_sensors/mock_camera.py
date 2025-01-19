import os
import sys
sys.path.append('/Users/aondo/Safelor/SafelorPi') 
class MockCamera:
    def __init__(self):
        # Mock test image path
        self.test_image_path = os.path.join(os.path.dirname(__file__), "/Users/aondo/Safelor/SafelorPi/scan_images/test_image.jpg")
        if not os.path.exists(self.test_image_path):
            raise FileNotFoundError(f"Test image not found at {self.test_image_path}")

    def capture_image(self):
        print(f"Mock Camera: Simulating image capture. Returning {self.test_image_path}")
        return self.test_image_path

    def check_image_for_ppe(self, image_id):
        print(f"Mock Model: Checking {image_id} for PPE compliance.")
        # Simulate PPE check result
        return ["hi-vis"] if "test_image" in image_id else []

    def check_image_for_face(self, image_id):
        print(f"Mock Model: Checking {image_id} for face detection.")
        # Simulate face detection result
        return True if "test_image" in image_id else False

    def perform_ppe_check(self, image_id):
        print(f"Mock Camera: Performing PPE check on {image_id}")
        emp_identified = self.check_image_for_face(image_id)
        emp_id = "12345" if emp_identified else None
        ppe_missing = self.check_image_for_ppe(image_id)
        return emp_id, emp_identified, ppe_missing
