from SafelorPi.pubnub_Pi.pubnub_client import PubNubClient
from SafelorPi.mongodb.mongo_client import MongoDBClient
from datetime import datetime
import os
import threading


def main():
    test_scan()

## this is an example of a successful scan, still working on facial detection
def test_scan():
    zone_id = 1
    mongodb = MongoDBClient()
    image_path = os.path.join(os.path.dirname(__file__), "scan_images", "noah_4.jpg")
    image_id = mongodb.upload_image(image_path)
    listening_channel = "roman_pi_recieve_results"
    # Any changes made to the requirements to the zone will be sent to this channel. 
    requirements_listening_channel = "zone1_get_requirements"
    response_event = threading.Event()
    requirements_response_event = threading.Event()
    message_container = {"response": None}   
    # a handler function to pass to the pubnub client, to signal to the app when recieved results from the server
    # will set the response event when the message is recieved
    def response_handler(message):
        message_container['response'] = message
        response_event.set() 
        
    def requirements_response_handler(message):
        message_container['response'] = message
        requirements_response_event.set() 
        
    
    pubnub = PubNubClient({listening_channel:response_handler,
                           requirements_listening_channel:requirements_response_handler})
    pubnub.subscribe_to_channel(listening_channel)
    pubnub.subscribe_to_channel(requirements_listening_channel)
    
    #Just send id of zone, server will handle the rest.
    pubnub.publish_message("zone_online_update",{"zone_id":zone_id})
    
    
    pubnub.publish_message("get_zone_requirements",{"zone_id":zone_id,"listening_channel":requirements_listening_channel})
    
    
    zone_requirements = []
    if requirements_response_event.wait(timeout=30): 
        print("Received response: ", message_container["response"])
        zone_requirements = message_container["response"]["zone_requirements"] or []
        print(zone_requirements)
    else:
        print("No response received for zone_requirements within the timeout.")
        
        
    # aswell as the imageid, should send a channel to specificy where the server should send the ppe detected result.
    # This allows for multiple pi's to use the same detection model channel.
    # Specify the zone id so server can check which ppe is required and tick off the found objects.
    # Boots might be returned in list of ppe not detected, but can be removed if detected on the pi-side.
    #The id's of ppe not detected will be returned in the channel!!
    image_to_be_checked = {
        "image_id":str(image_id),
        "listening_channel": listening_channel,
        "zone_id":zone_id
    }
    pubnub.publish_message("image_for_detection",image_to_be_checked)
    
    # this will hold the program until the response is recieved or the timeout completes
    # Specifiy the timeout as you see fit
    if response_event.wait(timeout=30): 
        print("Received response: ", message_container["response"])
        ppe_missing = message_container["response"]["id_ppe_not_detected"] or []
        emp_identified = message_container["response"]["face_detected"]
    else:
        print("No response received within the timeout.")
        ppe_missing = None
        emp_id_detected = None
    
    
    # response will contain missing ppe id's and emp id of employee detected. Emp id will be None if not detected.
    
    current_time = datetime.now()
    scan_data = {
        "zone_id":zone_id,
        "ppe_missing":ppe_missing,
        "data_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
        "HZoneEntered": True,
        "emp_identified": emp_identified,
        "scan_image_id" : str(image_id),
        "current_requirements": zone_requirements
    }
    
    
    pubnub.publish_message("scan_data_chan",scan_data)
    # unsubscribing will allow the script to stop.
    pubnub.unsubscribe_to_channel(listening_channel)
    
    
if __name__ == "__main__":
    main()
