#!/usr/bin/env python

import modules.ambient as ambient
import re
import pdb
import requests
import time
import json
import math
import numpy as np
import argparse
from subprocess import call
from datetime import datetime
import urllib

PARSER = argparse.ArgumentParser(description='Collect and report weather')
PARSER.add_argument('-p', '--password', metavar='password',
                    help='Weather underground password')
PARSER.add_argument('-s', '--station', metavar='station',
                    help='Weather underground station id (e.g. KCOFORTC100)')
ARGS = PARSER.parse_args()


WUNDER_PASS = ARGS.password
WUNDER_STN = ARGS.station

if WUNDER_STN is None or WUNDER_PASS is None:
    raise ValueError("Must provide station and password")

#print ambient.get_data("10.0.0.32", None)
PORT_KITCHEN=9000
PORT_BASEMENT=8000

IP_AMBIENT= "10.0.0.32"
IP_1WIRE_GAR = "10.0.0.74"
IP_1WIRE_BSM = "10.0.0.96"
PORT_OW_GAR = "9000"
PORT_OW_BSM = "8000"

LED_ON_URL = "http://" + IP_1WIRE_GAR + ":" + PORT_OW_GAR + \
             "/uncached/7E.B92E00001000/EDS0068/LED?control=2"
LED_OFF_URL = "http://" + IP_1WIRE_GAR + ":" + PORT_OW_GAR + \
             "/uncached/7E.B92E00001000/EDS0068/LED?control=0"
WIND_SPEED_THRESH = 20
WIND_GUST_THRESH = 30
DATA_FILE = "/var/www/html/newtemps.json"
WUNDER_HOST = "rtupdate.wunderground.com"

def get_dew_point_f(t_air_f, rel_humidity):
    a = 17.271
    b = 237.7 # degC
    t_air_f = float(t_air_f)
    rel_humidity = float(rel_humidity)
    T = float(5/9) * (float(t_air_f) - float(32))
    print "tempc: %s" % t_air_f
 
    Td = abs(b * gamma(T,rel_humidity)) / (a - gamma(T,rel_humidity))
    print "dewptc: %s" % Td
 
    return float(9/5) * Td + float(32)
 
 
def gamma(T,RH):
    a = 17.271
    b = 237.7 # degC
 
    g = (a * T / (b + T)) + np.log(RH/100.0)
 
    return g


def push_to_wunderground(wx, station, password):
    
    url = "http://" + WUNDER_HOST + "/weatherstation/updateweatherstation.php?ID=" + station + "&PASSWORD=" \
          + password \
          + "&tempf=" + wx['outside']['temp2'] \
          + "&humidity=" + wx['outside']['hum1'] \
          + "&dewptf=" + str(wx['outside']['dewpointf']) \
          + "&winddir=" + wx['outside']['winddir'] \
          + "&windspeedmph=" + wx['outside']['windspeedmph'] \
          + "&windgustmph=" + wx['outside']['windgustmph'] \
          + "&rainin=" + wx['outside']['rainin'] \
          + "&dailyrainin=" + wx['outside']['rainin'] \
          + "&weeklyrainin=" + wx['outside']['weeklyrainin'] \
          + "&monthlyrainin=" + wx['outside']['monthlyrainin'] \
          + "&yearlyrainin=" + wx['outside']['yearlyrainin'] \
          + "&baromin=" + wx['outside']['pressurein'] \
          + "&softwaretype=custom4" \
          + "&action=updateraw" \
          + "&realtime=1" \
          + "&dateutc=" + urllib.quote(str(wx['dateutc'])) \
          + "&rtfreq=5 HTTP/1.0"

    print url
    requests.get(url, verify=False)


def get_value_from_url(url, patt):
    val = (requests.get(url, verify=False)).text.strip()
    mat = re.match(patt, val, re.I)
    if mat:
        return mat.group(1)
    return None
    

def get_data(ip_ow_gar, port_ow_gar, ip_ow_bsm, port_ow_bsm, ip_amb, set_hazard_led=True):

    wx = {}

    ow_gar_base_url = "http://" + ip_ow_gar + ":" + port_ow_gar
    ow_bsm_base_url = "http://" + ip_ow_bsm + ":" + port_ow_bsm

    # Onewire sensor paths
    ktemp = get_value_from_url(ow_gar_base_url + 
            "/uncached/text/7E.B92E00001000/EDS0068/temperature", r'temperature\s+(\d+\.{0,1}\d+)')
    khum = get_value_from_url(ow_gar_base_url + "/uncached/text/7E.B92E00001000/EDS0068/humidity", r'humidity\s+(\d+\.{0,1}\d+)')
    gtemp = get_value_from_url(ow_gar_base_url + "/uncached/text/28.FF9A706A1403/temperature", r'temperature\s+(\d+\.{0,1}\d+)')
    outtemp = get_value_from_url(ow_bsm_base_url + "/uncached/text/10.193E4D010800/temperature", r'temperature\s+(\d+\.{0,1}\d+)')
    outhum = get_value_from_url(ow_bsm_base_url + "/uncached/text/26.80E4A8000000/humidity", r'humidity\s+(\d+\.{0,1}\d+)')

    amb = ambient.get_data(IP_AMBIENT, None)

    wx['dateutc'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print "date: %s" % wx['dateutc']
    wx['upstairs'] = {
                     'temp2': amb['weather']['indoortempf'],
                     'hum1': amb['weather']['indoorhumidity'],
                     }
    wx['kitchen'] = {
                     'temp1': ktemp, 
                     'hum1': khum, 
                    }
    wx['outside'] = {
                     'temp1': outtemp, 
                     'temp2': amb['weather']['tempf'],
                     'hum1': outhum,
                     'windgustmph': amb['weather']['windgustmph'],
                     'dailygust': amb['weather']['dailygust'],
                     'relpres': amb['weather']['RelPress'],
                     'windspeedmph': amb['weather']['windspeedmph'],
                     'winddir': amb['weather']['winddir'],
                     'pressurein': amb['weather']['RelPress'],
                     'rainin': amb['weather']['rainin'],
                     'hourlyrainin': amb['weather']['hourlyrainin'],
                     'monthlyrainin': amb['weather']['monthlyrainin'],
                     'weeklyrainin': amb['weather']['weeklyrainin'],
                     'yearlyrainin': amb['weather']['yearlyrainin'],
                     'hum2': amb['weather']['humidity'],
                     'dewpointf': get_dew_point_f(amb['weather']['tempf'], amb['weather']['humidity'])
                    }

#    if ( set_hazard_led ):
#        set_hazard_led(wx['outside']['windspeedmph'],
#                       wx['outside']['windgustmph'])

    push_to_wunderground(wx, WUNDER_STN, WUNDER_PASS)
    return wx


def set_hazard_led(wind_speed, wind_gust):
    if( wind_speed >= WIND_SPEED_THRESH or wind_gust >= WIND_GUST_THRESH ):
        requests.get(LED_ON_URL, verify=False)
        return
    requests.get(LED_OFF_URL, verify=False)


json_data = json.dumps(get_data(IP_1WIRE_GAR, PORT_OW_GAR, IP_1WIRE_BSM, PORT_OW_BSM, IP_AMBIENT))
with open(DATA_FILE, 'r') as original: data = original.read()
with open(DATA_FILE, 'w') as modified: modified.write(json_data + "\n" + data)
