from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import gridfs
from dotenv import load_dotenv

class MongoDBClient:
    def __init__(self):
        load_dotenv()
        self.client = None
        self.db = None
        self.user_collection = None
        self.fs = None
        self.connect()


    def connect(self):
        try:
            MONGO_PASSWORD = os.getenv('MONGODB_PASS')
            USER = os.getenv('MONGODB_USER')
            uri = f"mongodb+srv://{USER}:{MONGO_PASSWORD}@safelor.t47bg.mongodb.net/?retryWrites=true&w=majority&appName=Safelor"
            self.client = MongoClient(uri, server_api=ServerApi('1'))
            self.db = self.client['SafelorDB']
            self.fs = gridfs.GridFS(self.db)
            self.employee_collection = self.db['employee']
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")

    def upload_image(self, file_path, filename=None):
        try:
            with open(file_path, "rb") as image_file:
                file_id = self.fs.put(image_file, filename=os.path.basename(file_path))
            print(f"Image uploaded to GridFS with ID: {file_id}")
            return file_id
        except FileNotFoundError as e:
            print(f"Error uploading image: {e}")
        return None

    
    #This function is not required, temporary for uploading valid employees for use on front end
    def put_employee(self,employee_object):
        try:                                                       
            self.employee_collection.insert_one(employee_object)
            print("Employee Object Inserted")
        except Exception as e:
            print(f"Failed to insert employee Object to Mongodb: {e}")

    def get_ppe_names_by_ids(self, ids):
        query = {"ppe_id": {"$in": ids}}
        cursor = self.db['ppe'].find(query, {"name": 1, "_id": 0})
        ppe_names = [doc["name"] for doc in cursor]
        return ppe_names        

    def close(self):
        self.client.close()