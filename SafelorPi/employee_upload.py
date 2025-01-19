from SafelorPi.pubnub_Pi.pubnub_client import PubNubClient
from SafelorPi.pubnub_Pi.pubnub_client import PubNubClient
from SafelorPi.mongodb.mongo_client import MongoDBClient
from datetime import datetime
import os

pubnub = PubNubClient()
mongodb = MongoDBClient()

def main():
    test_scan()

def test_scan():
    
    image_path = os.path.join(os.path.dirname(__file__), "scan_images", "roman_ppe.jpg")
    image_id = mongodb.upload_image(image_path)
    current_time = datetime.now()
    employee = {
        "emp_id": 1008,
        "profile_image_id":image_id,
        "access_to":[1,2,3,4],
        "f_name":"Sean",
        "s_name":"Smith",
    }
    mongodb.put_employee(employee)
    print("After scan publish")


if __name__ == "__main__":
    main()
