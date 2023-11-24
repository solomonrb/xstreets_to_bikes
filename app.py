from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from datetime import datetime
import googlemaps
import requests
import math
import heapq
import os
import MySQLdb
import sshtunnel
from flask_executor import Executor

#to connect to DB
sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0

#to load in env variables
load_dotenv()
goog_auth_key = os.environ.get('GOOG_AUTH_KEY')
db_ssh_username = os.environ.get('DB_SSH_USERNAME')
db_ssh_password = os.environ.get('DB_SSH_PASSWORD')
db_remote_bind_address = os.environ.get('DB_REMOTE_BIND_ADDRESS')
db_user = os.environ.get('DB_USER')
db_passwd = os.environ.get('DB_PASSWD')
db_db = os.environ.get('DB_DB')

app = Flask(__name__)

#to make background tasks work
app.config['EXECUTOR_TYPE'] = 'thread'
app.config['EXECUTOR_POOL_RESTARTS'] = True
executor = Executor(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/command',methods=['POST'])
def command():
    address = request.form['Body']
    current_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    number = int(request.form['From'].replace("+", ""))
    
    target = get_curr_lat_long(address)

    if target != []:
        indexed_target = target[0]['geometry']['location']
        stations = get_station_locations()
        low_three = find_three_closest(indexed_target, stations)
        pre_string = get_low_three_status(low_three)
        converted = convert_to_string(pre_string)
    else:
        converted = "No Google Maps address found. Try cleaning up formatting like 'E 29 St and 1 Av' or 'Houston St and Macdougal St' or 'N 7 St and Bedford Av Williamsburg' with no extra words."

    #trigger in background to speed up response
    executor.submit(db_update_users(number))
    executor.submit(db_update_events(number,current_dt,address,converted))

    resp = MessagingResponse()
    resp.message(converted)
    return str(resp)


def get_curr_lat_long(address):
    corners = {'northeast': {'lat': 40.8518, 'lng': 73.7187}, 'southwest': {'lat': 40.5773, 'lng': 74.2282}}
    gmaps = googlemaps.Client(key=goog_auth_key)
    geocode_result = gmaps.geocode(address,bounds=corners)
    return geocode_result


def get_station_locations():
    r = requests.get('https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_information.json')
    stations = r.json()['data']['stations']
    stations_dict = {}
    for station in stations:
        stations_dict[station['station_id']] = {'lat':station['lat'],'lon':station['lon'],'name':station['name']}
    return stations_dict


def calc_euclidean_distance(target, station):
    dx = station['lat'] - target['lat']
    dy = station['lon'] - target['lng']
    distance = math.sqrt(dx**2 + dy**2)
    angle = math.atan2(dy, dx)
    angle_degrees = math.degrees(angle)
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    index = round(angle_degrees / 45) % 8
    cardinal = directions[index]
    return (distance, cardinal)


def find_three_closest(lat_lng_target, stations_dict):
    for station_id in stations_dict.keys():
        distance, cardinal = calc_euclidean_distance(lat_lng_target, stations_dict[station_id])
        stations_dict[station_id]['dist'] = distance
        stations_dict[station_id]['dir'] = cardinal
    low_three = dict(heapq.nsmallest(3, stations_dict.items(), key=lambda item: item[1]['dist']))
    return low_three


def get_low_three_status(low_three):
    r = requests.get('https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json')
    stations = r.json()['data']['stations']
    for station in stations:
        if station['station_id'] in low_three.keys():
            low_three[station['station_id']]['bikes_avail'] = station['num_bikes_available']
            low_three[station['station_id']]['ebikes_avail'] = station['num_ebikes_available']
            low_three[station['station_id']]['docks_avail'] = station['num_docks_available']
    return low_three


def convert_to_string(low_three):
    output_string = ""
    for station in low_three.keys():
        output_string += low_three[station]['name'] + " (" + low_three[station]['dir'] + ")" + " has " + str(low_three[station]['bikes_avail']) + " bikes, " + str(low_three[station]['ebikes_avail']) + " e-bikes, " + str(low_three[station]['docks_avail']) + " docks.\n"
    return output_string

    
def db_update_users(number):
    with sshtunnel.SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'),
        ssh_username=db_ssh_username, ssh_password=db_ssh_password,
        remote_bind_address=(db_remote_bind_address, 3306)
    ) as tunnel:
        conn = MySQLdb.connect(
            user=db_user,
            passwd=db_passwd,
            host='127.0.0.1', port=tunnel.local_bind_port,
            db=db_db,
        )
        cursor = conn.cursor()

        #the piece that changes
        check_user_query = "SELECT * FROM users WHERE phone = %s"
        check_user_values = (number,)
        cursor.execute(check_user_query, check_user_values)
        existing_user = cursor.fetchone()
        if existing_user:
            curr_phone, curr_text_count = existing_user 
            user_query = "UPDATE users SET phone = %s, text_count = %s WHERE phone = %s"
            user_values = (curr_phone, curr_text_count+1, curr_phone)
        else:
            user_query = "INSERT INTO users (phone, text_count) VALUES (%s, %s)"
            user_values = (number, 1)

        cursor.execute(user_query, user_values)
        conn.commit()
        cursor.close()
        conn.close()  


def db_update_events(phone, time, content, response):
    with sshtunnel.SSHTunnelForwarder(
        ('ssh.pythonanywhere.com'),
        ssh_username=db_ssh_username, ssh_password=db_ssh_password,
        remote_bind_address=(db_remote_bind_address, 3306)
    ) as tunnel:
        conn = MySQLdb.connect(
            user=db_user,
            passwd=db_passwd,
            host='127.0.0.1', port=tunnel.local_bind_port,
            db=db_db,
        )
        cursor = conn.cursor()

        # the piece that changes
        user_query = "INSERT INTO events (phone, time, content, response) VALUES (%s, %s, %s, %s)"
        user_values = (phone, time, content, response)

        cursor.execute(user_query, user_values)
        conn.commit()
        cursor.close()
        conn.close()  


if __name__ == "__main__":
  app.run()