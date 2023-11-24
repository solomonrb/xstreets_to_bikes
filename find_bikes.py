import googlemaps
import requests
import math
import heapq
import os
from dotenv import load_dotenv

#to load in env variables
load_dotenv()
goog_auth_key = os.environ.get('GOOG_AUTH_KEY')

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
    dy = target['lat'] - station['lat']
    dx = target['lng'] - station['lon']
    distance = math.sqrt(dx**2 + dy**2)
    return distance


def find_three_closest(lat_lng_target, stations_dict):
    for station_id in stations_dict.keys():
        stations_dict[station_id]['dist'] = calc_euclidean_distance(lat_lng_target, stations_dict[station_id])
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
        output_string += low_three[station]['name'] + " has " + str(low_three[station]['bikes_avail']) + " bikes, " + str(low_three[station]['ebikes_avail']) + " e-bikes, " + str(low_three[station]['docks_avail']) + " docks.\n"
    return output_string