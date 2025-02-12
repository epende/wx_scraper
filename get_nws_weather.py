import requests

# 40.5295483,-105.0568967 FOCO
# 31.3208,89.3856 KHBG

headers = {'User-Agent' : 'fouxbarre'}
endpoint = 'https://api.weather.gov/stations/KHBG/observations/latest'

response = requests.get(endpoint, headers = headers)
data = response.json()

print("tempf = %s" % int((9/5 * (float(data['properties']['temperature']['value']))) + 32))
print("windSpeed = %s" % (data['properties']['windSpeed']['value']))
print("precipitationLastHour = %s" % (data['properties']['precipitationLastHour']['value']))
print("relativeHumidity = %s" % (int(data['properties']['relativeHumidity']['value'])))
#print("= %s" % (data['properties']['']['value']))
