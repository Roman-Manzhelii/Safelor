from datetime import datetime
from threading import Thread
import time
from flask import Flask, render_template, request, url_for, redirect, jsonify,session, abort
from SafelorApp.pubnub.pubnub_client import PubNubClient
from SafelorApp.pubnub.handlers import Channel_Handler
from SafelorApp.mongodb.mongo_client import MongoDBClient
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow 
from pip._vendor import cachecontrol
import google.auth.transport.requests
import os
import pathlib
import requests
from functools import wraps
from cryptography.fernet import Fernet

app = Flask(__name__)

mongodb = MongoDBClient()
channel_handler = Channel_Handler(mongodb)
PUBNUB_CIPHER_KEY = Fernet.generate_key().decode()
print("Cipher key in flask server",PUBNUB_CIPHER_KEY)
pubnub = PubNubClient({"scan_data_chan":channel_handler.handle_scan_data_channel,
                       "image_for_detection":channel_handler.handle_image_for_detection_channel,
                       "get_zone_requirements":channel_handler.handle_get_zone_requirements,
                       "zone_online_update":channel_handler.handle_zone_online_update},
                      PUBNUB_CIPHER_KEY)
channel_handler.add_pubnub_client(pubnub)
pubnub.subscribe_to_channel("scan_data_chan")
pubnub.subscribe_to_channel("image_for_detection")
pubnub.subscribe_to_channel("get_zone_requirements")
pubnub.subscribe_to_channel("zone_online_update")
app.secret_key = os.getenv("SECRET_FLASK_KEY")

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SECRET_API_KEY = os.getenv('SECRET_API_KEY')
GOOGLE_CLIENT_ID =(os.getenv("GOOGLE_CLIENT_ID"))
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "google_auth_secrets.json")


flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes = ["https://www.googleapis.com/auth/userinfo.profile","https://www.googleapis.com/auth/userinfo.email","openid"],
    redirect_uri = "http://127.0.0.1:5000/login/authorized"
)

offline_threshold =  100 #100 second threshold for zone online check

def check_for_offline_zones():
    while True:
        zones = list(mongodb.get_all_zones())
        current_time = time.time()
        for zone in zones:
            if 'last_online' in zone:
                if (current_time-zone['last_online'])>offline_threshold and zone['online_status']==True: 
                    mongodb.update_zone_online_status(zone['zone_id'],False)
                    zone_status = mongodb.get_zone_online_status()
                    zone_status_map = {}
                    for zone in zone_status:
                        zone_status_map[zone['zone_id']] = zone['online_status']
                    pubnub.publish_message("return_online_status",{'zone_status_map':zone_status_map})
            else: #Handle zones that dont currently have the last online field (New zones added)
                mongodb.update_zone_last_online(zone['zone_id'],0)
                mongodb.update_zone_online_status(zone['zone_id'],False)
        time.sleep(60)
                   
                   
offline_monitor_thread = Thread(target=check_for_offline_zones, daemon=True)
offline_monitor_thread.start()
    
    
def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
             return redirect("/unauthorized")
        else:
            return function(*args, **kwargs) 
    return wrapper


@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"An error occurred: {e}"
        # return redirect("/unauthorized")


@app.route('/get_cipher_key', methods=['POST'])
def get_cipher_key():
    #Check if the user has been authenticated
    print("Attempting cipher request")
    if "google_id" in session:  
        print("Cipher key sent to client",PUBNUB_CIPHER_KEY)
        return jsonify({"cipher_key": PUBNUB_CIPHER_KEY})
     # Or check if the pi has the secret pi key
    elif request.headers.get("Authorization") == SECRET_API_KEY:
         return jsonify({"cipher_key": PUBNUB_CIPHER_KEY})
    else:   
        return jsonify({"error": "Unauthorized"})
 
    
@app.route('/get_notifications', methods=['POST'])
def get_notifications():
    print("Attempting cipher request")
    if "google_id" in session:  
        unchecked_notifications = mongodb.get_unchecked_ppe_scans()
        print("Returning unchecked scans in get notifications route")
        for notification in unchecked_notifications:
            if "_id" in notification:
                notification["_id"] = str(notification["_id"])
        return jsonify({"notifications": unchecked_notifications})
    else:
        return jsonify({"error": "Unauthorized"})
    
      
@app.route("/get_pubnub_token", methods=['POST'])
def get_pubnub_token():
    #Check if the user has been authenticated
    if "google_id" in session: 
        token_result = pubnub.generate_token_client()
        if token_result:
            return jsonify({"token": token_result})
    # Or check if the pi has the secret pi key
    elif request.headers.get("Authorization") == SECRET_API_KEY:
        token_result = pubnub.generate_token_pi()
        return jsonify({"token": token_result})
    else:
        return jsonify({"error": "Unauthorized"})


@app.route("/unauthorized")
def unauthorized_route():
    try:
        return render_template('unauthorized.html')
    except Exception as e:
        return f"An error occurred: {e}"
 

@app.route("/login")
def login():
    try:
        return redirect("/zones")
    except Exception as e:
        return redirect("/unauthorized")


@app.route('/zone_status_request', methods=['POST'])
def zone_status_request():
    if "google_id" in session:
        zone_status = mongodb.get_zone_online_status()
        zone_status_map = {}
        for zone in zone_status:
            zone_status_map[zone['zone_id']] = zone['online_status']
        return jsonify({"zone_status_map": zone_status_map})
    else:
        return jsonify({"error": "Unauthorized"}), 401
    

@app.route("/google_login")
def google_login():
    try:
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        return redirect(authorization_url)
    except Exception as e:
        print("Error with google login ",e)
        return redirect("/unauthorized")
    

@app.route("/logout")
def logout():
    try:
        session.clear()
        return redirect("/")
    except Exception as e:
        return redirect("/")
 

@app.route('/login/authorized')
def authorized():
    flow.fetch_token(authorization_response=request.url)
    if not session["state"] == request.args["state"]:
        abort(500)
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session = cached_session)
    
    id_info = id_token.verify_oauth2_token(
        id_token = credentials._id_token,
        request = token_request,
        audience = GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info.get("sub")
    print(session["google_id"])
    session["name"] = id_info.get("name")
    session['email'] = id_info.get('email')
    user = mongodb.get_user_by_email(session['email'])
    print(session['email'])
    print(session["name"])
    if user is None:
        session.clear()
        # return "Invalid User"
        return redirect("/unauthorized")
    return redirect(url_for('zones'))



@app.route("/users")
@login_is_required
def users():
    try:
        users = mongodb.get_users()
        return render_template('users.html', users=users)
    except Exception as e:
        return redirect("/unauthorized")
        # return f"An error occurred: {e}"
    
    
@app.route("/ppe_scan", methods=['POST','GET'])
@login_is_required
def invalidppe():
    try:
        print("scan id from js",request.args.get('scan_id'))
        scan_id = request.args.get('scan_id')
        scan_object = mongodb.get_scan_by_id(scan_id)
        image_data = mongodb.get_image_gridfs(scan_object['scan_image_id'])
        return render_template('ppe_scan.html',scan_object=scan_object,image_data=image_data,scan_id=scan_id)
    except Exception as e:
        # return f"An error occurred: {e}"
        return redirect("/unauthorized")
    
    
@app.route("/check_scan", methods=['POST'])
@login_is_required
def check_scan():
        print("scan id from js",request.args.get('scan_id'))
        scan_id = request.args.get('scan_id')
        scan_id = mongodb.update_scan_checked(scan_id)
        if scan_id is not None:
            return jsonify({"response": "success"})
        else:
            return jsonify({"response": "failure"})
        

@app.route("/send_warning/<emp_id>", methods=['POST'])
@login_is_required
def send_warning(emp_id):
    try:
        latest_scan_image = mongodb.get_latest_ppe_scan_violation(emp_id)
        emp_email = mongodb.get_employee_email_by_id(emp_id)
        user_name = session['name']
        email = session['email']
        message = "This is a warning, invalid ppe detected in a scan recently."
        timestamp = datetime.now()
        notification = {
            'emp_id':int(emp_id),
            'recipient_email':emp_email,
            'scan_image_id':str(latest_scan_image.get("scan_image_id")),
            'message':message,
            'sender_name':user_name,
            'sender_email':email,
            'timestamp':timestamp,
            'resolved':False,
            'sent':False
        }
        mongodb.insert_notification(notification)
        return jsonify({"response": "success"}),200

    except Exception as e:
        print("An error occured in send warning :",e)
        return jsonify({"error": str(e)}), 500


        
   
@app.route("/employee", methods=['POST','GET'])
@login_is_required
def employee():
    try:
        employee_id = request.args.get('employee_id')
        emp_object = mongodb.get_employee(employee_id)
        image_data = mongodb.get_image_gridfs(emp_object['profile_image_id'])
        emp_scans = mongodb.get_scans_by_empid(employee_id)
        employee_stats = mongodb.get_employee_statistics(employee_id)
        if len(employee_stats) != 0:
            employee_stats = employee_stats[0]
        else:
            employee_stats = {}
        return render_template('employee.html',employee=emp_object,image_data=image_data,emp_scans=emp_scans,emp_stats=employee_stats)
    except Exception as e:
        print("Error redirecting to /employee : ",e)
        return redirect("/unauthorized")

       
@app.route("/zones")
@login_is_required
def zones():
    try:
        zones = mongodb.get_all_zones()
        ppe = mongodb.get_all_ppe()
        ppe_map = {item['ppe_id']: item for item in ppe}
        return render_template('zones.html', zones=zones, ppe = ppe_map)
    except Exception as e:
        print("Exception in zones ",e)
        return redirect("/unauthorized")
    

@app.route("/employees")
@login_is_required
def employees():
    try:
        employees = list(mongodb.get_all_employee())
        zones = mongodb.get_all_zones()
        zone_map = {item['zone_id']: item for item in zones}
        return render_template('employees.html', employees=employees,zone_map=zone_map)
    except Exception as e:
        print("Exception in zones ",e)
        return redirect("/unauthorized")
   
    
@app.route("/zone")
@login_is_required
def zone():
    try:
        zone_id = request.args.get('zone_id')
        zone = mongodb.get_zone_by_id(int(zone_id))
        scans = mongodb.get_scans_by_zone(int(zone_id))
        zone_stats = mongodb.get_zone_statistics(zone_id)
        if len(zone_stats) > 0:
            zone_stats = zone_stats[0]
        else:
            zone_stats = {} 
        return render_template('zone.html', zone=zone, scans=scans,zone_stats=zone_stats)
    except Exception as e:
        print("Error redirecting to zones : ",e)
        return redirect("/unauthorized")
        # return f"An error occurred: {e}"
     
        
@app.route("/zone_settings")
@login_is_required
def zone_settings():
    try:
        zone_id = request.args.get('zone_id')
        zone = mongodb.get_zone_by_id(zone_id)
        ppe_ids = zone.get('ppe_required')
        return render_template('zone_setting.html',required_ppe = ppe_ids, zone_id=zone_id, zone = zone)
    except Exception as e:
        # return redirect("/unauthorized")
        return f"zone_settings: {e}"
        

@app.route("/update_requirements" , methods=['POST'])
@login_is_required
def update_requirements():
    try:
        zone_id = request.form.get('zone_id') 
        required_ppe = request.form.getlist('required_ppe')
        required_ppe = list(map(int, required_ppe))
        mongodb.update_zone_requirements(zone_id, required_ppe)
        pubnub.publish_message("zone"+zone_id+"_get_requirements",{"zone_requirements":required_ppe})
        return redirect('/zones')
    except Exception as e:
        # return redirect("/unauthorized")
        return f"update_requirements: {e}"
    


@app.errorhandler(404)
def not_found(error):
    return render_template('notfound.html'), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

