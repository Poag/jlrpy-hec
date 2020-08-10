#!/usr/bin/python3

import jlrpy
from configparser import ConfigParser
import os
import json
import requests
import time

config = ConfigParser()
config.read('config.ini')

username = config.get('jlrpy', 'email')
password = config.get('jlrpy', 'password')
url = config.get('influxdb', 'url')
verify_ssl = config.get('jlrpy', 'insecure_ssl')
index = config.get('influxdb', 'db')
epoch_time = int(time.time())

if verify_ssl == "True":
    ssl_verify = True
else:
    ssl_verify = False

# Authenticate using the username and password
c = jlrpy.Connection(username, password)
v = c.vehicles[0]
user_info = c.get_user_info()
status = v.get_status()

healthstatus = v.get_health_status()
status = { d['key'] : d['value'] for d in v.get_status()['vehicleStatus'] }
position = v.get_position()

json_status = status
json_health = healthstatus
json_position = position

# Generate the JSON
json_out = {
    "time": epoch_time,
    "index": index,
    "source": "jlrpy",
    "event": [
    {"Full Health": json_health},
    {"Full Status": json_status},
    {"Position": json_position}
    ]
}
print(json.dumps(json_out))
