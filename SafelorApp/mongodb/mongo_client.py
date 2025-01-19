from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
import gridfs
import base64
from datetime import datetime
from functools import wraps


class MongoDBClient:
    def __init__(self):
        load_dotenv()
        self.client = None
        self.db = None
        self.user_collection = None
        self.ppe_scan_collection = None
        self.zone_collection = None
        self.ppe_collection = None
        self.employee_collection = None
        self.log_collection = None
        self.fs = None
        self.connect()


    def connect(self):
        try:
            # Get MongoDB credentials from environment 
            MONGO_PASSWORD = os.getenv('MONGODB_PASS')
            self.USER = os.getenv('MONGODB_USER')
            uri = f"mongodb+srv://{self.USER}:{MONGO_PASSWORD}@safelor.t47bg.mongodb.net/?retryWrites=true&w=majority&appName=Safelor"
            self.client = MongoClient(uri, server_api=ServerApi('1'))
            self.db = self.client['SafelorDB']
            self.user_collection = self.db['user']
            self.employee_collection = self.db['employee']
            self.ppe_scan_collection = self.db['ppe_scan']
            self.zone_collection = self.db['zone']
            self.ppe_collection = self.db['ppe']
            self.log_collection = self.db['logs']
            self.notification_collection = self.db['notification']
            self.fs = gridfs.GridFS(self.db)
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")


    def mongo_log(action, collection):
        def decorator(function):
            @wraps(function)
            def wrapper(self, *args, **kwargs):
                try:
                    result = function(self, *args, **kwargs)
                    self.log_db_operation(action=action, collection=collection, status="SUCCESS", returned=str(result), user=self.USER)
                    return result
                except Exception as e:
                    self.log_db_operation(action=action, collection=collection, status="FAILURE", returned=None, user=self.USER)
                    print(f"Error logging MongoDB action: {e}")
            return wrapper
        return decorator


    def log_db_operation(self,action, collection,status, returned="",user="",):
        log_entry = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "action": action,
        "status":status,
        "collection": collection,
        "returned": returned,
        "user":user
        }
        self.log_collection.insert_one(log_entry)


    @mongo_log(action="FIND", collection="user")
    def get_users(self):
        if self.user_collection is not None:
            try:
                users = list(self.user_collection.find({}, {"_id": 0}))
                return users
            except Exception as e:
                print(f"Error retrieving users: {e}")
                return []
    
    
    @mongo_log(action="AGGREGATE", collection="ppe_scan")    
    def get_employee_statistics(self, empId):
        print("Getting employee statistics")
        match = { 
            "$match": { 
                "emp_id": int(empId)
            } 
        }
        group,project = self.statistic_pipeline_items()
        pipeline = [match, group, project]
        result = list(self.ppe_scan_collection.aggregate(pipeline))
        print("Get employee statistics result ->", result)
        return result
    
    @mongo_log(action="AGGREGATE", collection="ppe_scan")    
    def get_zone_statistics(self, zone_id):
        print("Getting zone_id statistics")
        match = { 
            "$match": { 
                "zone_id": int(zone_id)
            } 
        }
        group,project = self.statistic_pipeline_items()
        pipeline = [match, group, project]
        result = list(self.ppe_scan_collection.aggregate(pipeline))
        print("Get zone statistics result ->", result)
        return result
    
    def statistic_pipeline_items(self):
        group = { 
            "$group": { 
                "_id": "$zone_id", 
                "totalScans": { "$sum": 1 },  # Count all scans
                "scansWithMissingPPE": { 
                    "$sum": { 
                        "$cond": [
                            { 
                                "$and": [ 
                                    { "$eq": ["$HZoneEntered", True] }, 
                                    { "$gt": [{ "$size": { "$ifNull": ["$ppe_missing", []] } }, 0] } 
                                ] 
                            },
                            1,
                            0
                        ] 
                    } 
                } 
            } 
        }
        project = { 
            "$project": { 
                "emp_id": "$_id", 
                "totalScans": 1, 
                "scansWithMissingPPE": 1, 
                "percentageMissingPPE": { 
                    "$multiply": [{ "$divide": ["$scansWithMissingPPE", "$totalScans"] }, 100] 
                } 
            } 
        }
        return group,project
    

    @mongo_log(action="INSERT", collection="notification")
    def insert_notification(self,notification):
        try:
            result = self.notification_collection.insert_one(notification)
            return result
        except Exception as e:
            print(f"Error inserting notification: {e}")
            return None
        
        
    @mongo_log(action="FIND", collection="ppe_scan")
    def get_latest_ppe_scan_violation(self,emp_id):
        try:
            latest_scan = list(self.ppe_scan_collection.find({"emp_id": int(emp_id),"$expr": {"$gt": [{ "$size": "$ppe_missing" }, 0]}}).sort("data_time", -1).limit(1))
            print(f"latest scan for emp {emp_id}",latest_scan)
            return latest_scan[0]
        except Exception as e:
            print(f"Error getting latest scan: {e}")
            return None


    @mongo_log(action="INSERT_ONE", collection="user")
    def insert_user(self, user_data):
        try:
            result = self.user_collection.insert_one(user_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error inserting user: {e}")
            return None
        

    @mongo_log(action="INSERT_ONE", collection="user")
    def get_employee_email_by_id(self, id):
        try:
            result = self.employee_collection.find_one({'emp_id':int(id)},{'_id':0,'work_email':1})
            print("Employee email retrieved from MONGO :",result)
            return result['work_email']
        except Exception as e:
            print(f"Error inserting user: {e}")
            return None
        
        
    @mongo_log(action="FIND", collection="zone")
    def get_all_zones(self):
        if self.zone_collection is not None:
            try:
                zones = self.zone_collection.find()
                return zones
            except Exception as e:
                print(f"Error retrieving zones: {e}")
                return []
            
            

    def update_zone_last_online(self,zone_id,last_online):
        try:
            zone_updated = self.zone_collection.update_one({"zone_id":zone_id}, {"$set": {"last_online": last_online}})
            if zone_updated != None:
                return True
            return False
        except Exception as e:
            print(f"Error updating zone last_online : {e}")
            return False
        
        
    def update_zone_online_status(self,zone_id,online_status):
        try:
            zone_updated = self.zone_collection.update_one({"zone_id":zone_id}, {"$set": {"online_status": online_status}})
            if zone_updated != None:
                return True
            return False
        except Exception as e:
            print(f"Error updating zone online_status : {e}")
            return False
      
      
    def get_zone_online_status(self):
        try:
            zones = list(self.zone_collection.find({},{'zone_id':1,'online_status':1,'_id':0}))
            return zones
        except Exception as e:
            print(f"Error updating zone online_status : {e}")
            return []
            
    @mongo_log(action="FIND", collection="ppe")
    def get_all_ppe(self):
        if self.zone_collection is not None:
            try:
                ppe = self.ppe_collection.find()
                return ppe
            except Exception as e:
                print(f"Error retrieving ppe: {e}")
                return []
   
   
    @mongo_log(action="INSERT_ONE", collection="ppe_scan")
    def upload_scan(self, scan_object):
        try:
            result = self.ppe_scan_collection.insert_one(scan_object)
            inserted_id = result.inserted_id  
            print("Scan Object Inserted with ID:", inserted_id)
            return str(inserted_id)
        except Exception as e:
            print(f"Failed to insert scan Object to MongoDB: {e}")
            return None
      
        
    @mongo_log(action="FIND_ONE", collection="ppe_scan")
    def get_scan_by_id(self, id):
        try:
            print("Scan id ",id)
            ppe_scan = self.ppe_scan_collection.find_one({"_id":ObjectId(id)})
            print("Scan Object Retrieved by ID:", ppe_scan)
            return ppe_scan
        except Exception as e:
            print(f"Failed to retrieve scan Object from MongoDB: {e}")
            return None
        
        
    @mongo_log(action="UPDATE_ONE", collection="ppe_scan")
    def update_scan_checked(self, id):
        try:
            print("Scan id ",id)
            ppe_scan = self.ppe_scan_collection.update_one({"_id":ObjectId(id)}, {"$set": {"checked": True}})
            print("Scan Object updated :", ppe_scan)
            return ppe_scan
        except Exception as e:
            print(f"Failed to update scan Object with checked: {e}")
            return None
       
        
    @mongo_log(action="GET", collection="GRIDFS")
    def get_image_gridfs(self, id):
        try:
            image_file = self.fs.get(ObjectId(id))
            print("Image file from GRIDFS",image_file)
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            mime_type = image_file.content_type
            image_data = f"data:{mime_type};base64,{image_base64}"
            return image_data
        
        except Exception as e:
            return f"Image not found: {e}", 404
      
        
    @mongo_log(action="FIND_ONE", collection="employee")
    def get_employee(self, id):
        try:
            print(id)
            employee = self.employee_collection.find_one({"emp_id":int(id)})
            print("Employee Object Retrieved by ID:", employee)
            return employee
        except Exception as e:
            print(f"Failed to retrieve employee Object from MongoDB: {e}")
            return None
       
        
    @mongo_log(action="FIND_ONE", collection="employee")
    def get_employee(self, id):
        try:
            print(id)
            employee = self.employee_collection.find_one({"emp_id":int(id)})
            print("Employee Object Retrieved by ID:", employee)
            return employee
        except Exception as e:
            print(f"Failed to retrieve employee Object from MongoDB: {e}")
            return None
     
        
    @mongo_log(action="FIND", collection="ppe_scan")   
    def get_scans_by_empid(self,empid):
        try:
            scans = self.ppe_scan_collection.find({"emp_id": int(empid)}).sort("data_time", -1)
            scans_list = list(scans)
            print("Retrieved scans")
            return scans_list
        except Exception as e:
            print(f"Failed to retrieve scan objects from MongoDB: {e}")
            return None
      
        
    @mongo_log(action="FIND_ONE", collection="zone")
    def get_zone_by_id(self,zone_id):
        try:
            zone = self.zone_collection.find_one({"zone_id": int(zone_id)})
            print("Retrieved zone",zone)
            return zone
        except Exception as e:
            print(f"Failed to retrieve zone from MongoDB: {e}")
            return None
        
    @mongo_log(action="FIND", collection="ppe_scan")
    def get_unchecked_ppe_scans(self):
        try:
            scans = list(self.ppe_scan_collection.find({"checked": False, "$expr": {"$gt": [{ "$size": "$ppe_missing" }, 0]}}).sort("data_time", 1))
            print("Retrieved unchecked scans",scans)
            return scans
        except Exception as e:
            print(f"Failed to retrieve zone from MongoDB: {e}")
            return None
        
    @mongo_log(action="FIND", collection="ppe")
    def get_zone_requirements(self,ppe_id_list):
        try:
            ppe_list = list(self.ppe_collection.find({"ppe_id":{"$in": ppe_id_list}},{"ppe_id": 1,"_id":0}))
            print("Retrieved zone_requirements",ppe_list)
            return ppe_list
        except Exception as e:
            print(f"Failed to retrieve zone_ppe_requireents from MongoDB: {e}")
            return None
       
        
    @mongo_log(action="FIND", collection="ppe_scan")
    def get_scans_by_zone(self,zone_id):
        try:
            scans = list(self.ppe_scan_collection.find({"zone_id": int(zone_id)}).sort("data_time", -1))
            print("Retrieved scans",scans)
            return scans
        except Exception as e:
            print(f"Failed to retrieve scans by zone from MongoDB: {e}")
            return None
     
        
    @mongo_log(action="FIND_ONE", collection="ppe")
    def get_ppe_by_id(self,ppe_id):
        try:
            ppe = self.ppe_collection.find_one({"ppe_id": int(ppe_id)})
            print("Retrieved ppe ",ppe)
            return ppe
        except Exception as e:
            print(f"Failed to retrieve ppe by ppe_id from MongoDB: {e}")
            return None
      
    
    @mongo_log(action="FIND", collection="employee")
    def get_all_employee(self):
        try:
            employees = list(self.employee_collection.find())
            print("Retrieved employees ",employees)
            return employees
        except Exception as e:
            print(f"Failed to retrieve all employee from MongoDB: {e}")
            return None
    
    
    @mongo_log(action="FIND_ONE", collection="user")
    def get_user_by_email(self,email):
        try:
            user = self.user_collection.find_one({"email":email})
            print("Retrieved user ",user)
            return user
        except Exception as e:
            print(f"Failed to user by email from MongoDB: {e}")
            return None
        

    @mongo_log(action="UPDATE_ONE", collection="zone")
    def update_zone_requirements(self,zone_id,ppe_ids):
        try:
            result = self.zone_collection.update_one({"zone_id":int(zone_id)},{"$set":{"ppe_required":ppe_ids}})
            if result.matched_count > 0:
                print("Updated zone ppe requirements")
            else:
                print("No match when updating ppe zone requirements")
        except Exception as e:
            print(f"Failed to update zone ppe_requirements on MongoDB: {e}")
        
        
        
