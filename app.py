from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import googlemaps
import requests
import math
import heapq
import os

#load_dotenv('.env') commenting out for github push
#goog_auth_key = os.environ.get('GOOG_AUTH_KEY') commenting out for github push
goog_auth_key = os.getenv('GOOG_AUTH_KEY')
gmaps = googlemaps.Client(key=goog_auth_key)

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/command',methods=['POST'])
def command():
    address = request.form['Body']
    
    target = get_curr_lat_long(address)
    stations = get_station_locations()
    low_five = find_five_closest(target, stations)
    pre_string = get_low_five_status(low_five)
    converted = convert_to_string(pre_string)

    resp = MessagingResponse()
    resp.message(converted)
    return str(resp)

def get_curr_lat_long(address):
    corners = {'northeast': {'lat': 40.8518, 'lng': 73.7187}, 'southwest': {'lat': 40.5773, 'lng': 74.2282}}
    geocode_result = gmaps.geocode(address,bounds=corners)
    return geocode_result[0]['geometry']['location']

def get_station_locations():
    r = requests.get('https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_information.json')
    stations = r.json()['data']['stations']
    stations_dict = {}
    for station in stations:
        stations_dict[station['station_id']] = {'lat':station['lat'],'lon':station['lon'],'name':station['name']}
    return stations_dict

def calc_euclidean_distance(target, station):
    dy = target['lat'] - station['lat']
    dx = target['lng'] - station['lon']
    distance = math.sqrt(dx**2 + dy**2)
    return distance

def find_five_closest(lat_lng_target, stations_dict):
    for station_id in stations_dict.keys():
        stations_dict[station_id]['dist'] = calc_euclidean_distance(lat_lng_target, stations_dict[station_id])
    low_five = dict(heapq.nsmallest(5, stations_dict.items(), key=lambda item: item[1]['dist']))
    return low_five

def get_low_five_status(low_five):
    r = requests.get('https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json')
    stations = r.json()['data']['stations']
    for station in stations:
        if station['station_id'] in low_five.keys():
            low_five[station['station_id']]['bikes_avail'] = station['num_bikes_available']
            low_five[station['station_id']]['ebikes_avail'] = station['num_ebikes_available']
            low_five[station['station_id']]['docks_avail'] = station['num_docks_available']
    return low_five

def convert_to_string(low_five):
    output_string = ""
    for station in low_five.keys():
        output_string += low_five[station]['name'] + " has " + str(low_five[station]['bikes_avail']) + " bikes, " + str(low_five[station]['ebikes_avail']) + " e-bikes, " + str(low_five[station]['docks_avail']) + " docks.\n"
    return output_string
    

    
if __name__ == "__main__":
  app.run()