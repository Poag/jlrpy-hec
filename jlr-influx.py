#!/usr/bin/python3

from configparser import ConfigParser
from datetime import datetime
import json
import os
from pprint import pprint
import time
from typing import Any

import jlrpy
import requests
from influxdb import InfluxDBClient
from typer import Exit, echo, secho, colors, run


class Log:

    @staticmethod
    def error(log: Any):
        secho('[ERROR] %s' % str(log), fg=colors.RED)

    @staticmethod
    def info(log: Any):
        secho('[INFO] %s' % str(log), fg=colors.GREEN)

    @staticmethod
    def warning(log: Any):
        secho('[WARNING] %s' % str(log), fg=colors.YELLOW)


config = ConfigParser()
config.read('config.ini')

username = config.get('jlrpy', 'email')
password = config.get('jlrpy', 'password')
verify_ssl = config.get('jlrpy', 'insecure_ssl')

IDB_HOST = config.get('influxdb', 'host')
IDB_PORT = config.get('influxdb', 'port')
IDB_DBNAME = config.get('influxdb', 'db')
IDB_USER = config.get('influxdb', 'user')
IDB_PASSWORD = config.get('influxdb', 'pass')


def get_data():
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
    json_position = dict()
    for k in position['position']:
        json_position['position-' + k] = position['position'][k]

    fields = dict()
    fields.update(json_health)
    fields.update(json_status)
    fields.update(json_position)

    json_out = [
        {
            "measurement": "jlrpy-out",
            "tags": {
                "vechicle": "ipace",
                "region": "eu"
            },
            "time": datetime.now(),
            "fields": fields
        }
    ]
    return json_out


def get_influxdb() -> InfluxDBClient:
    client = InfluxDBClient(IDB_HOST, IDB_PORT, IDB_USER, IDB_PASSWORD, IDB_DBNAME)
    client.create_database(IDB_DBNAME)
    return client


def main():
    Log.info("Started.")

    Log.info("Getting data from JLR Car API ...")
    json_data = get_data()

    Log.info("Connecting to InfluxDB ...")
    try:
        client = get_influxdb()
    except Exception as e:
        Log.error(e)
        raise Exit

    Log.info("Saving data to InfluxDB ...")
    try:
        client.write_points(json_data)
    except Exception as e:
        Log.error(e)
        raise Exit

    Log.info("Completed.")


if __name__ == '__main__':
    run(main)
