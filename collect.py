#!/usr/bin/env python

from lxml import html
import argparse
import json
import re
import time
import sys

import requests

PARSER = argparse.ArgumentParser(description='Collect from Observer IP module')
PARSER.add_argument('-i', '--ip', metavar='ip',
                    help='IP address of Observer IP module')
PARSER.add_argument('-u', '--url', metavar='url',
                    help='Full URL of Observer IP module (optional)')

ARGS = PARSER.parse_args()

IP = ARGS.ip
if IP is None and url is None:
    raise ValueError("Must provide one of --ip or --url options")

if IP:
    observer_url = "http://" + IP + "/livedata.htm"

if ARGS.url:
    observer_url = ARGS.url

page = requests.get(observer_url, verify=False)
tree = html.fromstring(page.content)

names = tree.xpath('//input[@name]/@name')
values = tree.xpath('//input[@name]/@value')

if (len(names) != len(values)):
    raise IndexError("Unexpected html structure")

# Device to standard name translation
name_table = {'windir':  'winddir',
              'avgwind':  'windspeedmph',
              'outHumi':  'humidity',
              'AbsPress':  'baromin',
              'rainofhourly':  'hourlyrainin',
              'rainofdaily':  'rainin',
              'rainofweekly':  'weeklyrainin',
              'rainofmonthly':  'monthlyrainin',
              'rainofyearly':  'yearlyrainin',
              'inHumi':  'indoorhumidity',
              'avgwind':  'windspeedmph',
              'gustspeed':  'windgustmph',
              'inTemp':  'indoortempf',
              'outTemp':  'tempf',
              'CurrTime':  'device_time',
              }

pairs = {}
weather = {'weather': pairs}
weather['time'] = time.time()
weather['url'] = observer_url

for name, value in zip(names, values):
    # Use fuzzy matching on names in case they change
    if re.search('temp', name, re.I):
        pairs[name_table[name]] = value

    if re.search('curr', name, re.I) and re.search('time', name, re.I):
        pairs[name_table[name]] = value

    if re.search('pres', name, re.I):
        pairs[name] = value

    if re.search('humi', name, re.I):
        pairs[name_table[name]] = value

    if re.search('uv', name, re.I):
        pairs[name] = value

    if re.search('solar', name, re.I):
        pairs[name] = value

    if re.search('rain', name, re.I) and re.search('of', name, re.I):
        pairs[name_table[name]] = value

    if re.search('gust', name, re.I) or re.search('wind', name, re.I):
        if name in name_table:
            pairs[name_table[name]] = value
        else:
            pairs[name] = value

for name, value in pairs.iteritems():
    if re.search(r'--', value):
        pairs[name] = None

print json.dumps(weather)
