# -*- coding: utf-8 -*-
import logging, json, time

from src import etc, cfg

import paho.mqtt.publish as publish


def pubConn(device_id, state):
    st = {0: 'offline', 1: 'online'}
    state = st.get(state)
    try: 
        publish.single(cfg.server['OKO_PREF'] + '/' + str(device_id) + "/connect/main", payload=state, qos=1, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']})
        logging.debug(f"Avbl main msg send OK {device_id} {state}")
        return True
    except Exception as err:
        logging.error(f"Failed to connect to MQTT server\n{err}")
        return False

def pubConnEx(device_id, ex_id, state):
    st = {0: 'offline', 1: 'online'}
    state = st.get(state)
    try: 
        publish.single(cfg.server['OKO_PREF'] + '/' + str(device_id) + '/connect/ex' + str(ex_id), payload=state, qos=1, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']})
        logging.debug(f"Avbl ex msg send OK {device_id} ex{ex_id} {state}")
        return True
    except Exception as err:
        logging.error(f"Failed to connect to MQTT server\n{err}")
        return False