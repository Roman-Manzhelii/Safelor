from SafelorApp.mongodb.mongo_client import MongoDBClient
from SafelorApp.pubnub.pubnub_client import PubNubClient
from SafelorApp.detection_model.ppe_detection_model import PPE_Detection_Model
from SafelorApp.detection_model.employee_detection import is_face_match
import time
import numpy as np
from PIL import Image
import io
import base64
import face_recognition

class Channel_Handler:
    def __init__(self, mongodb_client: MongoDBClient):
        self.mongodb_client = mongodb_client
        self.ppe_detection_model = PPE_Detection_Model()

    def add_pubnub_client(self, client : PubNubClient):
        self.pubnub_client = client
        
    def handle_get_zone_online_status(self):
        zone_status = self.mongodb_client.get_zone_online_status()
        zone_status_map = {}
        for zone in zone_status:
            zone_status_map[zone['zone_id']] = zone['online_status']
        self.pubnub_client.publish_message("return_online_status",{'zone_status_map':zone_status_map})
        
                        
    def handle_scan_data_channel(self, data):
        print(f"Handling scan data channel: {data}")    
        data['checked'] = False
        if data['emp_identified']:
            image_id = data.get('scan_image_id')
            image = self.mongodb_client.get_image_gridfs(image_id)
            emp_id_detected = self.find_employee_match(image)
            data['emp_id'] = emp_id_detected
        object_id = self.mongodb_client.upload_scan(data)
        print("scan id in handler to client",object_id)
        if data['HZoneEntered']==True and len(data['ppe_missing'])>0:
            print("HZONE ENTERED AND REQUIRED PPE MISSING")
            self.pubnub_client.publish_message("ppe_violation",{"scan_id":object_id,})
        else:
            print("Notification not sent, no violation!")
         
    
    def handle_zone_online_update(self,data):
        print(f"Handling zone_online update: {data}") 
        zone_id = data['zone_id']
        last_online_status = time.time()
        self.mongodb_client.update_zone_last_online(zone_id,last_online_status)
        self.mongodb_client.update_zone_online_status(zone_id,True)
        zone_status = self.mongodb_client.get_zone_online_status()
        zone_status_map = {}
        for zone in zone_status:
            zone_status_map[zone['zone_id']] = zone['online_status']
        self.pubnub_client.publish_message("return_online_status",{'zone_status_map':zone_status_map})
        
                 
    def handle_get_unchecked_scans(self):
        print(f"Handling get unckecked scans channel")    
        unchecked_scans = self.mongodb_client.get_unchecked_ppe_scans()
        print("unchecked scans in handle get unchecked scans",unchecked_scans)
        self.pubnub_client.publish_message("recieve_unchecked_scans",{"unchecked_scans":unchecked_scans})
    
    def handle_get_zone_requirements(self,data):
        zone_id = data.get('zone_id')
        pi_listening_channel = data.get('listening_channel')
        zone = self.mongodb_client.get_zone_by_id(zone_id)
        ppe_ids = zone.get('ppe_required')
        print("\nGot zone requirements ",ppe_ids)
        self.pubnub_client.publish_message(pi_listening_channel,{"zone_requirements":ppe_ids})
        
    def handle_change_zone_requirements(self,data):
        zone_id = data.get('zone_id')
        ppe_requirements = data.get('ppe_requirements')
        print("\nGot zone requirements :",ppe_requirements)
        self.mongodb_client.update_zone_requirements(zone_id,ppe_requirements)
        

    #This function will return the id's of ppe required that has not been detected!!!
    def handle_image_for_detection_channel(self, data):
        start = time.time()
        print(f"Handling image_for_detection channel: {data}")  
        image_id = data.get('image_id')
        pi_listening_channel = data.get('listening_channel')
        zone_id = data.get("zone_id")
        image = self.mongodb_client.get_image_gridfs(image_id)
        predicted_classes = self.ppe_detection_model.get_predicted_objects(image)
        zone_object = self.mongodb_client.get_zone_by_id(zone_id)
        required_ppe = []
        for id in zone_object.get('ppe_required'):
            ppe = self.mongodb_client.get_ppe_by_id(id)
            required_ppe.append(ppe)
        id_ppe_not_detected = []
        for ppe in required_ppe:
            if ppe['name'] not in predicted_classes:
                id_ppe_not_detected.append(ppe['ppe_id'])
        print("Id's of ppe not detected! ",id_ppe_not_detected)
        face_detected = self.is_face_detected(image)
        # emp_id_detected = self.find_employee_match(image)
        results = {
            "id_ppe_not_detected":id_ppe_not_detected,
            "face_detected":face_detected
        }
        end = time.time()
        print("TIME TO EXECUTE ->>>>",end-start)
        self.pubnub_client.publish_message(pi_listening_channel,results)
       
      
    def is_face_detected(self,scan_image):
        image1_bytes = self.decode_image(scan_image)
        image1 = Image.open(io.BytesIO(image1_bytes))
        image1 = np.array(image1)
        image1_encodings = face_recognition.face_encodings(image1)
        if not image1_encodings:
            print("No face detected in the first image.")
            return False
        return True
        
 # Turns out this is very slow. Especially if we have to sift through many employees for the scan.
 # Should bring it up with Roman about possibly doing face checks after scan is uploaded.     
    def find_employee_match(self,scan_image):
        image1_bytes = self.decode_image(scan_image)
        image1 = Image.open(io.BytesIO(image1_bytes))
        image1 = np.array(image1)
        image1_encodings = face_recognition.face_encodings(image1)
        employees = self.mongodb_client.get_all_employee()
        for emp in employees:
            emp_profile_img = self.mongodb_client.get_image_gridfs(emp['profile_image_id'])
            found_face = is_face_match(image1_encodings,emp_profile_img)
            if found_face:
                return emp['emp_id']
        return None
    
    
    def does_face_exist(self,scan_image):
        image1_bytes = self.decode_image(scan_image)
        image1 = Image.open(io.BytesIO(image1_bytes))
        image1 = np.array(image1)
        image1_encodings = face_recognition.face_encodings(image1)
        if not image1_encodings:
            print("No face detected in the first image.")
            return "No Face"         
    
    def decode_image(self,data_uri):
        base64_data = data_uri.split(",")[1]
        return base64.b64decode(base64_data)
            
            
        
        
