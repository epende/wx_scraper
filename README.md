# Weather Scraper
Scrapes weather data from Ambient Weather IP Observer module

This module collects weather data from the Observer's local
web interface and outputs formatted json.
Tested using WS-0900-IP, firware version 4.4.2 on SUSE Linux

Requirements:  lxml parser (and its dependencies).  This should work on Windows and Mac, but I have only tested it with Linux.

Example usage:
./collect.py -i 10.0.0.32
{"url": "http://10.0.0.32/livedata.htm", "weather": {"windir": "88", "outHumi": "49", "AbsPress": "25.05", "rainofmonthly": "0.28", "unit_time": "17:04 5/15/2018", "RelPress": "27.61", "uv": "---", "solarrad": "----.-", "dailygust": "8.1", "outTemp": "71.8", "uvi": "--", "inTemp": "71.8", "rainofyearly": "0.28", "inHumi": "47", "rainofweekly": "0.26", "gustspeed": "1.3", "rainofhourly": "0.00", "rainofdaily": "0.00", "avgwind": "0.0"}, "time": 1526421898.964183}
