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
import socket

# Predefined Smart Plug Commands
# For a full list of commands, consult tplink_commands.txt
commands = {'info'     : '{"system":{"get_sysinfo":{}}}',
                        'on'       : '{"system":{"set_relay_state":{"state":1}}}',
                        'off'      : '{"system":{"set_relay_state":{"state":0}}}',
                        'cloudinfo': '{"cnCloud":{"get_info":{}}}',
                        'wlanscan' : '{"netif":{"get_scaninfo":{"refresh":0}}}',
                        'time'     : '{"time":{"get_time":{}}}',
                        'schedule' : '{"schedule":{"get_rules":{}}}',
                        'countdown': '{"count_down":{"get_rules":{}}}',
                        'antitheft': '{"anti_theft":{"get_rules":{}}}',
                        'reboot'   : '{"system":{"reboot":{"delay":1}}}',
                        'reset'    : '{"system":{"reset":{"delay":1}}}'
}

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

PORT_KITCHEN=9000
PORT_BASEMENT=8000

IP_AMBIENT= "44.20.8.32"
IP_1WIRE_GAR = "44.20.6.55"
IP_1WIRE_BSM = "44.20.6.22"
IP_COFFEE = "44.20.6.77"
IP_FAN = "44.20.6.29"
PORT_OW_GAR = "8000"
PORT_OW_BSM = "8000"

#LED_ON_URL = "http://" + IP_1WIRE_GAR + ":" + PORT_OW_GAR + \
#             "/uncached/7E.B92E00001000/EDS0068/LED?control=2"
#LED_OFF_URL = "http://" + IP_1WIRE_GAR + ":" + PORT_OW_GAR + \
#             "/uncached/7E.B92E00001000/EDS0068/LED?control=0"
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
          + "&tempf=" + str(wx['outside']['temp2']) \
          + "&humidity=" + str(wx['outside']['hum2']) \
          + "&dewptf=" + str(wx['outside']['dewpointf']) \
          + "&winddir=" + str(wx['outside']['winddir']) \
          + "&windspeedmph=" + str(wx['outside']['windspeedmph']) \
          + "&windgustmph=" + str(wx['outside']['windgustmph']) \
          + "&rainin=" + str(wx['outside']['rainin']) \
          + "&dailyrainin=" + str(wx['outside']['rainin']) \
          + "&weeklyrainin=" + str(wx['outside']['weeklyrainin']) \
          + "&monthlyrainin=" + str(wx['outside']['monthlyrainin']) \
          + "&yearlyrainin=" + str(wx['outside']['yearlyrainin']) \
          + "&baromin=" + str(wx['outside']['pressurein']) \
          + "&softwaretype=custom4" \
          + "&action=updateraw" \
          + "&realtime=1" \
          + "&dateutc=" + urllib.quote(str(wx['dateutc'])) \
          + "&rtfreq=5 HTTP/1.0"

    print url
    requests.get(url, verify=False)


def get_value_from_url(url, patt):
    print url
    val = (requests.get(url, verify=False)).text.strip()
    mat = re.match(patt, val, re.I)
    if mat:
        return mat.group(1)
    return None

# Check if IP is valid
def validIP(ip):
        try:
                socket.inet_pton(socket.AF_INET, ip)
        except socket.error:
                parser.error("Invalid IP Address.")
        return ip 


# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
def encrypt(string):
        key = 171
        result = "\0\0\0\0"
        for i in string: 
                a = key ^ ord(i)
                key = a
                result += chr(a)
        return result

def decrypt(string):
        key = 171 
        result = ""
        for i in string: 
                a = key ^ ord(i)
                key = ord(i) 
                result += chr(a)
        return result

def send_tplink(ip, port, cmd):
    # Send command and receive reply 
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.connect((ip, port))
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        sock_tcp.close()
    
        print "Sent:     ", cmd
        print "Received: ", decrypt(data[4:])
        return decrypt(data[4:])
    except socket.error:
        quit("Cound not connect to host " + ip + ":" + str(port))
    
    

#def get_data(ip_ow_bsm, port_ow_bsm, ip_amb, set_hazard_led=True):
def get_data(ip_ow_gar, port_ow_gar, ip_ow_bsm, port_ow_bsm, ip_amb, set_hazard_led=True):

    wx = {}

    coffee_state = json.loads(send_tplink(IP_COFFEE, 9999, commands['info']))['system']['get_sysinfo']['relay_state']
    print "coffee:  "
    print coffee_state
    fan_state = json.loads(send_tplink(IP_FAN, 9999, commands['info']))['system']['get_sysinfo']['relay_state']

    ow_gar_base_url = "http://" + ip_ow_gar + ":" + port_ow_gar
    ow_bsm_base_url = "http://" + ip_ow_bsm + ":" + port_ow_bsm

    # Onewire sensor paths
    ktemp = get_value_from_url(ow_gar_base_url + 
            "/uncached/text/7E.B92E00001000/EDS0068/temperature", r'temperature\s+(\d+\.{0,1}\d+)')
    khum = get_value_from_url(ow_gar_base_url + "/uncached/text/7E.B92E00001000/EDS0068/humidity", r'humidity\s+(\d+\.{0,1}\d+)')
    gtemp = get_value_from_url(ow_gar_base_url + "/uncached/text/28.FF9A706A1403/temperature", r'temperature\s+(\d+\.{0,1}\d+)')
    outtemp = get_value_from_url(ow_bsm_base_url + "/uncached/text/10.193E4D010800/temperature", r'temperature\s+(\d+\.{0,1}\d+)')
    outtemp = None
    outhum = get_value_from_url(ow_bsm_base_url + "/uncached/text/26.80E4A8000000/humidity", r'humidity\s+(\d+\.{0,1}\d+)')
    outhum = None

    amb = ambient.get_data(IP_AMBIENT, None)

    wx['dateutc'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    wx['datesec'] = time.time()
    print "date: %s" % wx['dateutc']
    wx['upstairs'] = {
                     'temp2': amb['weather']['indoortempf'],
                     'hum1': amb['weather']['indoorhumidity'],
                     'fan':  fan_state,
                     }
    wx['kitchen'] = {
                     'coffee':  coffee_state,
                     'temp1':  ktemp,
                     'hum1':  khum,
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


#json_data = json.dumps(get_data(IP_1WIRE_BSM, PORT_OW_BSM, IP_AMBIENT))
json_data = json.dumps(get_data(IP_1WIRE_GAR, PORT_OW_GAR, IP_1WIRE_BSM, PORT_OW_BSM, IP_AMBIENT))
with open(DATA_FILE, 'r') as original: data = original.read()
with open(DATA_FILE, 'w') as modified: modified.write(json_data + "\n" + data)
