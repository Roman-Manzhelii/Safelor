import face_recognition
import numpy as np
from PIL import Image
import io
import base64


#https://pypi.org/project/face-recognition/ <-- face recognition documentation


def is_face_match(image_to_check_encodings, image_to_compare):
    image2_bytes = decode_image(image_to_compare)
    face_encoding1 = image_to_check_encodings[0]
    image2 = Image.open(io.BytesIO(image2_bytes))
    image2 = np.array(image2)
    image2_encodings = face_recognition.face_encodings(image2)
    face_encoding2 = image2_encodings[0]
    results = face_recognition.compare_faces([face_encoding1], face_encoding2)
    print("Results ", results)
    if results[0]:
        print("Matched profile")
    else:
        print("Did not match profile")
    return results[0]
     
             
def decode_image(data_uri):
    base64_data = data_uri.split(",")[1]
    return base64.b64decode(base64_data)