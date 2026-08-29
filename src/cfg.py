# -*- coding: utf-8 -*-
import logging, json

import coloredlogs

from src import etc


DEFAULT_SERVER_CONFIG = {
  "SOCKET_PORT": 31200,
  "SOCKET_TIMEOUT": 90,
  "SOCKET_IP": "0.0.0.0",
  "SOCKET_LISTEN": 5,
  "MQTT_USER": " ",
  "MQTT_PASSWORD": " ",
  "MQTT_IP": "127.0.0.1",
  "MQTT_PORT": 1883,
  "OKO_PREF": "oko",
  "AD_ENBL": True,
  "AD_PREF": "homeassistant",
  "AD_ENBL_HOMED": False,
  "AD_PREF_HOMED": "homed",
  "LOG_LEVEL": 30
}

server_config = etc.read_JSON_file('./config/server.json')
if server_config == False:
    server_config = dict(DEFAULT_SERVER_CONFIG)
    etc.write_JSON_file(server_config, './config/server.json')
    logging.warning("Default server config saved")
else:
    # fill in new params missing from an existing config file, without touching values already set by the user
    missing = {key: value for key, value in DEFAULT_SERVER_CONFIG.items() if key not in server_config}
    if missing:
        server_config.update(missing)
        etc.write_JSON_file(server_config, './config/server.json')
        logging.warning(f"Server config updated with new params: {list(missing)}")


devices_config = etc.read_JSON_file('./config/devices.json')
if devices_config == False:
    devices_config = json.loads('[]')
    etc.write_JSON_file(devices_config, './config/devices.json')
    logging.warning("Clear devices config saved")

server = server_config
devices = devices_config

def search_device(imei):
    for device in devices:
        if device['imei'] == str(imei):
            return device

def logs():
    coloredlogs.DEFAULT_LOG_LEVEL = server['LOG_LEVEL']
    coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'white'}, 'levelname': {'bold': True, 'color': 'black'}, 'threadName': {'color': 'magenta'}, 'process': {'color': 'yellow'}}
    coloredlogs.install(fmt='%(asctime)s.%(msecs)03d  %(levelname)-8s %(threadName)-11s %(process)d %(message)s', datefmt='%H:%M:%S')
    