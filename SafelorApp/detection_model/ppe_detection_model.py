from ultralytics import YOLO
from pathlib import Path
from PIL import Image
import io
import base64

class PPE_Detection_Model:
    def __init__(self):
        self.current_dir = Path(__file__).parent
        best_model_weights = self.current_dir / "best.pt"
        self.model = YOLO(best_model_weights)

    def get_predicted_objects(self,ppe_scan_image):
        # Scan image is in uri form, must decode back to base64 to be readable by the model.
        base64_data = ppe_scan_image.split(',')[1]
        image_data = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_data))
        results = self.model.predict(source=image, conf=0.25)
        predicted_classes = [self.model.names[int(cls)] for cls in results[0].boxes.cls]
        for cls in predicted_classes:
            print(cls)
        return predicted_classes