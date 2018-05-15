# Weather Scraper
Scrapes weather data from Ambient Weather IP Observer module

This module collects weather data from the Observer's local
web interface and outputs formatted json.
Tested using WS-0900-IP, firware version 4.4.2 on SUSE Linux

Requirements:  lxml parser (and its dependencies).  This should work on Windows and Mac, but I have only tested it with Linux.

Example usage:
./collect.py -i 10.0.0.32
{"url": "http://10.0.0.32/livedata.htm", "weather": {"device_time": "17:44 5/15/2018", "windgustmph": "5.4", "AbsPress": "25.04", "uvi": null, "indoorhumidity": "43", "hourlyrainin": "0.00", "RelPress": "27.60", "uv": null, "solarrad": null, "rainin": "0.00", "humidity": "48", "winddir": "0", "windspeedmph": "1.3", "monthlyrainin": "0.28", "yearlyrainin": "0.28", "weeklyrainin": "0.26", "dailygust": "8.1", "indoortempf": "74.7", "tempf": "72.5"}, "time": 1526424294.206133}
