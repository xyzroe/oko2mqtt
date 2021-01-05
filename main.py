#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import socket
import json
from threading import Thread
from multiprocessing import Process
from datetime import datetime

import coloredlogs
from bitstring import BitArray
from deepdiff import DeepDiff
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe

def write_JSON_file(object, file):
    with open(file, 'w', encoding="utf-8") as json_file:
        json_file.write(json.dumps(object, indent=4, ensure_ascii=False))

def read_JSON_file(file):
    try:
        with open(file, encoding="utf-8") as json_file:
            return json.load(json_file)
    except:
        logging.error("Error open "+ str(file))
        return False

def scan_msg(msgData):

    def parse_msg_to_json(msg):

        #dev_state = {}


        if len(msg) > 45:
            cuts = str(msg[msg.find("{") + 1 :msg.find("}")]).split(",")
            logging.debug(cuts)
            logging.debug('New message lenth is ' + str(len(msg)) + ' symbols and consists of ' + str(len(cuts)) + ' cuts')
            if len(cuts) == 37:
                def byte2bits(byte):
                    z = hex(byte)
                    if (byte < 15):z = '0' + z
                    z = BitArray(hex=z)
                    return z
                def byte2temp(byte):
                    z = byte
                    if (byte == 128):z =  ''
                    elif (byte > 125):z =  byte - 256
                    return z
                def bytes2adc(bytes):
                    z = round(3.28 * 10 * int('0x' + bytes, 16) / 4095 , 2)
                    return z
                def bytes2radio(bytes):
                    device_type = int(bytes[3][0:1], 16)
                    switcher = {
                         1:'{ "alarm":false, "tamper":false, "low_battery":false, "test":false, "sensor_type": "magnet"  }',
                        11:'{ "alarm":false, "tamper":false, "low_battery":false, "test":false, "sensor_type": "event"  }',
                         9:'{ "alarm":false, "tamper":false, "low_battery":false, "test":false, "sensor_type": "fire"  }',
                         5:'{ "sos":false, "open":false, "close":false, "home":false, "sensor_type": "remote_simple"  }',
                        13:'{ "sos":false, "open":false, "close":false, "home":false, "sensor_type": "remote"  }',
                        14:'{ "alarm":false, "tamper":false, "low_battery":false, "test":false, "temp":0, "sensor_type": "temp_extender"  }',
                        10:'{ "alarm":false, "tamper":false, "low_battery":false, "test":false, "temp":0, "sensor_type": "temp"  }'
                    }
                    z = json.loads(switcher.get(device_type, "{}"))
                    if (device_type > 0):
                        bits = byte2bits(int('0x' + bytes, 16)).bin
                    if (device_type == 1) or (device_type == 11) or (device_type == 9) or (device_type == 14) or (device_type == 10):
                        z['tamper'] = str(int(bool(int(bits [7+1]))))
                        z['alarm'] = str(int(bool(int(bits [7+2]))))
                        z['low_battery'] = str(int(bool(int(bits [7+3]))))
                        z['test'] = str(int(bool(int(bits [7+4]))))
                    if (device_type == 14) or (device_type == 10):
                        z['temp'] = str(int(byte2temp(int(bytes[0:2], 16))))
                    if (device_type == 5) or (device_type == 13):
                        z['sos'] = str(int(bool(int(bits [7+1]))))
                        z['open'] = str(int(bool(int(bits [7+2]))))
                        z['home'] = str(int(bool(int(bits [7+3]))))
                        z['close'] = str(int(bool(int(bits [7+4]))))
                    return z

                def cut2bits(cut, obj):
                    bits = byte2bits(bytes.fromhex(cut)[1])
                    i = 0
                    while i < 8:
                        obj[i]['state'] = str(int(bits[7-i]))
                        i += 1

                def cut2mode(cut):
                    bytess = bytes.fromhex(cut)[1]
                    #print (bytess)
                    switcher = {
                         0:'disarmed',
                         1:'armed_away',
                         2:'armed_home',
                         4:'armed_night'
                    }
                    return switcher.get(bytess, "unknown")


                def cut2inputs(cut, obj):

                    in_alarm = byte2bits(bytes.fromhex(cut)[1])
                    in_cut = byte2bits(bytes.fromhex(cut)[2])
                    in_short = byte2bits(bytes.fromhex(cut)[3])

                    i = 0
                    while i < 8:
                        obj[i]['alarm'] = str(int(in_alarm[7-i]))
                        obj[i]['cut'] = str(int(in_cut[7-i]))
                        obj[i]['short'] = str(int(in_short[7-i]))
                        i += 1
                def cut2dallas(cut, obj):
                    i = 0
                    while i < 8:
                        if byte2temp(bytes.fromhex(cut)[i]):
                            obj[i]['value'] = str(byte2temp(bytes.fromhex(cut)[i]))
                        i += 1
                def cut2adcs(cut, obj):
                    i = 0
                    while i < 5:
                        obj[i]['value'] = str(round(bytes2adc(cut[(i * 4):(i * 4 + 4)]),1))
                        i += 1
                def cut2radios(cut, obj):
                    i = 0
                    while i < 16:
                        obj[i] = bytes2radio(cut[(i * 4):(i * 4 + 4)])
                        i += 1
                def cuts2counters(start_cut_id, obj):
                    i = 0
                    while i < 8:
                        if cuts[start_cut_id+i]: obj[i]['count'] = str(int(cuts[start_cut_id+i]))
                        i += 1

                def cut2general(obj):
                    general_state = byte2bits(int(cuts[3][0:2], 16))
                    #print(general_state)
                    obj[0]['tamper'] = str(int(general_state[4-1]))
                    obj[1]['power'] = str(int(general_state[2-1]))
                    obj[2]['bat12v'] = str(int(general_state[3-1]))
                    obj[3]['bat5v'] = str(int(general_state[5-1]))
                    obj[4]['gsm'] = str(-113 + (int(cuts[5], 16) * 2)) #to dBm
                    obj[5]['code'] = str(int(cuts[1], 16))
                    obj[6]['txt'] = msg_codes[int(cuts[1], 16)]
                    obj[7]['balance'] = cuts[11]
                    obj[8]['siren'] = str(int(bool(byte2bits(bytes.fromhex(cuts[4])[0])[7])))
                    obj[9]['armed'] = str(int(bool(bytes.fromhex(cuts[2])[1])))

                def cuts2address(start_cut_id, obj):
                    i = 0
                    while i < 8:
                        if cuts[start_cut_id+i]: obj[0+i]['value'] = cuts[start_cut_id+i]
                        i += 1

                def cuts2others(obj):
                    if cuts[28] or cuts[29]:
                        #obj['system-data'] = {}
                        obj[6]['type'] = cuts[28]
                        obj[7]['value'] = cuts[29]
                    if cuts[30]: obj[1]['value'] = cuts[30] #ex1
                    if cuts[31]: obj[2]['value'] = cuts[31] #ex2
                    if cuts[32]: obj[3]['value'] = cuts[32] #ex3
                    if cuts[33]: obj[4]['value'] = cuts[33] #ex4
                    if cuts[34]: obj[0]['value'] = cuts[34] #ex0
                    if cuts[35]: obj[5]['value'] = cuts[35] #radio_sockets

                dev_state = read_JSON_file('./dev/clean.json')
                #print (dev_state)
                dev_state['imei'] = cuts[0]
                dev_state['hw'] = cuts[10]
                dev_state['sw'] = cuts[9]
                dev_state['mode'] = cut2mode(cuts[2])
                #print(str(dev_state['imei']) + " " + str(dev_state['hw']) + " " + str(dev_state['sw']))
                #pprint(dev_state)
                cut2general(dev_state['general'])
                cut2bits(cuts[2], dev_state['groups'])

                cut2inputs(cuts[3], dev_state['inputs'])
                cut2bits(cuts[4], dev_state['outputs'])
                cut2dallas(cuts[6], dev_state['dallas'])
                cut2radios(cuts[7], dev_state['radios'])
                cut2adcs(cuts[8], dev_state['adcs'])
                cuts2counters(12, dev_state['counters'])

                cuts2address(20, dev_state['address-sensors'])

                cuts2others(dev_state['others'])
                #cut2ex_in(30, dev_state['ex1_in'])
                #cut2ex_out(30, dev_state['ex1_out'])
                #cut2ex_in(31, dev_state['ex2_in'])
                #cut2ex_out(31, dev_state['ex2_out'])
                #cut2ex_in(32, dev_state['ex3_in'])
                #cut2ex_out(32, dev_state['ex3_out'])
                #cut2ex_in(33, dev_state['ex4_in'])
                #cut2ex_out(33, dev_state['ex4_out'])

                logging.debug(dev_state)
                return dev_state
            else:
                return None

    def update_device_config_value(key, old, new):
        for device in devices_config:
            if device[key] == old:
                device[key] = str(new)
                return True

    newMsg = parse_msg_to_json(msgData)
    if newMsg:
        device_config = search_device_config(newMsg['imei'])
        if device_config:

            publish.single(server_config['OKO_PREF'] + '/' + str(device_config['id']) + '/' + "cmnd", payload='', qos=1, retain=1, hostname=server_config['MQTT_IP'], port=server_config['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':server_config['MQTT_USER'], 'password':server_config['MQTT_PASSWORD']})

            if (device_config['sw'] != newMsg['sw']):
                logging.warning("[" + str(device_config['id']) + "] New firmware [" + newMsg['sw'] + " vs " + device_config['sw'] + "] Check all then update config")

            statusInit = True
            for device_status in devices_status:
                if device_status['imei'] == newMsg['imei']:
                    statusInit = False
                    logging.info('[' + device_config['id'] + '] Message recived')
                    compare_device_status(device_status, newMsg)
                    return device_config['id'], device_config['pin']

            if statusInit:
                devices_status.append(read_JSON_file('./dev/clean.json'))
                for device_status in devices_status:
                    if device_status['imei'] == "0":
                        device_status['imei'] = newMsg['imei']
                        logging.info('[' + device_config['id'] + '] Device config found')
                        compare_device_status(device_status, newMsg)
                        return device_config['id'], device_config['pin']


        else:
            devices_config.append(read_JSON_file('./dev/clean.json'))
            update_device_config_value('imei', '0', newMsg['imei'])
            update_device_config_value('hw', '0', newMsg['hw'])
            update_device_config_value('sw', '0', newMsg['sw'])
            logging.warning('New device, type ' + newMsg['hw'] + ' v' + newMsg['sw'] + ' with IMEI ' + newMsg['imei'])
            write_JSON_file(devices_config, './config/devices.json')
            return scan_msg(msgData)

def search_device_config(imei):
    for device in devices_config:
        if device['imei'] == str(imei):
            return device

def work_with_value (imei, action, key, value):

    def key_extract_from_string(key):
        type = str(key[key.find("[") + 1 : key.find("]")])
        type = str(type[1 : -1])
        z = str(key[key.find("]") + 1 : ])
        id = str(z[z.find("[") + 1 : z.find("]")])
        if id.isdigit():
            kei = str(z[z.find("]") + 2 : -1])
            kei = str(kei[1 : -1])
            return type, int(id), kei
        else:
            id = str(id[1 : -1])
            return type, " ", id

    def init_device_sensor(type, id, ke, value):
        if type == "general":
            name = {
                 0:'Тампер',
                 1:'Источник питания',
                 2:'12B аккумулятор',
                 3:'Li-ion аккумулятор',
                 4:'Уровень GSM',
                 5:'Статус код',
                 6:'Статус',
                 7:'Баланс',
                 8:'Сирена',
                 9:'Режим охраны'
            }
            icon = {
                 0:'safety',
                 1:'plug',
                 2:'battery',
                 3:'battery',
                 4:'signal_strength',
                 5:'mdi:message-processing',
                 6:'mdi:message-processing-outline',
                 7:'mdi:cash-usd',
                 8:'mdi:alarm-light',
                 9:'mdi:security',
            }
            #return
            if int(id) < 5:
                return json.loads('{ "name":"' + str(name.get(int(id), '')) + '","class":"' + str(icon.get(int(id), '')) + '" }')
            else:
                return json.loads('{ "name":"' + str(name.get(int(id), '')) + '","icon":"' + str(icon.get(int(id), '')) + '" }')
        elif type == "inputs":
            if ke == "alarm":
                if int(id) < 4:
                    return json.loads('{ "name":"Вход '+str(id+1)+'","class":"window","short":true,"cut":true }')
                else:
                    return json.loads('{ "name":"","class":"","short":false,"cut":false }')
            else:
                return False
        elif type == "groups":
            if 2 < int(id) < 6:
                return json.loads('{ "name":"Группа '+str(id+1)+'","icon":"mdi:group" }')
            else:
                return json.loads('{ "name":"","icon":"" }')
        elif type == "outputs":
            if 0 < int(id) < 3:
                return json.loads('{ "name":"Выход '+str(id+1)+'","icon":"mdi:flash" }')
            else:
                return json.loads('{ "name":"","icon":"" }')
        elif type == "adcs":
            if 0 < int(id) < 3:
                return json.loads('{ "name":"ADC '+str(id+1)+'","icon":"mdi:speedometer" }')
            else:
                return json.loads('{ "name":"","icon":"" }')
        elif type == "dallas":
            return json.loads('{ "name":"DS18B20 '+str(id+1)+'","class":"temperature" }')
        elif type == "radios":
            if ke == "sensor_type":
                return json.loads('{ "name":"","class":"","sensor_type":"'+value+'" }')
            else:
                return False
        else:
            return json.loads('{ "name":"" }')

    def update_device_status_value(imei, type, id, ke, value):
        for device_status in devices_status:
            if device_status['imei'] == str(imei):
                if type != 'mode':
                    device_status[type][int(id)][ke] = value
                else:
                    device_status[type] = value
                if value:
                    make_msg_status(imei, type, id, ke, value)

    #print(key)
    type, id, ke = key_extract_from_string(key)
    #print(type, id, ke, value, action)
    if (type != 'sw') and (type != 'hw') and (type != 'imei'):
        if action == "A":
            for device in devices_config:
                if device['imei'] == str(imei):
                    if type == 'mode':
                        #print ("[" + str(action) +  "]", type, value)
                        update_device_status_value(imei, type, id, ke, value)
                        if server_config['AD_ENBL'] == True: make_msg_discovery(imei, type, id, ke)
                    else:
                        #current = str(device[type][int(id)])
                        if str(device[type][int(id)]) == '{}':
                            beta = init_device_sensor(type, id, ke, value)
                            if beta != False:
                                device[type][int(id)] = beta
                        try:
                            if str(device[type][int(id)]['name']):
                                #print ("[" + str(action) +  "]", type, id, ke, value)
                                #print (str(device[type][int(id)]['name']))
                                if type == 'inputs':
                                    if (ke == "cut") or (ke == "short"):
                                        #print(str(device[type][int(id)][str(ke)]))
                                        if bool(device[type][int(id)][str(ke)]) == False:
                                            #print ("_FALSE_")
                                            update_device_status_value(imei, type, id, ke, value)
                                            break
                                #print ("_TRUE_")
                                update_device_status_value(imei, type, id, ke, value)
                                if server_config['AD_ENBL'] == True: make_msg_discovery(imei, type, id, ke)#,, value device)
                        except:
                            pass



                        #except:
                            #pass
        if action == "U":
            for device in devices_config:
                if device['imei'] == str(imei):
                    if type != 'mode':
                        if device[type][int(id)]['name']:
                            #print ("[" + str(action) +  "]", type, id, ke, value)
                            update_device_status_value(imei, type, id, ke, value)
                    else:
                            #print ("[" + str(action) +  "]", type, value)
                            update_device_status_value(imei, type, id, ke, value)
        if action == "D":
            pass

def make_msg_discovery(imei, type, id, ke):
    current_device = search_device_config(imei)
    if type != 'mode':
        UID = str(server_config['OKO_PREF'] + '_' + current_device['id'] + '/' + str(type) + '_' + str(id+1))
        UID2 = str(server_config['OKO_PREF'] + '/' + current_device['id'] + '/' + str(type) + '/' + str(id+1))
        name = current_device[type][int(id)]['name']

        if type == 'general':
            ad_dev = '"avty_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/connect/state", "device":{"identifiers":"' + str(imei) + '"}'
            try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
            except: pass
            try: ad_dev = ad_dev + ', "icon":"' + current_device[type][int(id)]['icon'] + '"'
            except: pass
            general_msgs = {
                0: (server_config['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/tamper", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                1: (server_config['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/power", "pl_off":"0", "pl_on":"1", ' + ad_dev + '}', 1, True),
                2: (server_config['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/bat12v", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                3: (server_config['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/bat5v", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                4: (server_config['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/gsm", "unit_of_meas":"dBm", ' + ad_dev + '}', 1, True),
                5: (server_config['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/code", "unit_of_meas":" ", ' + ad_dev + '}', 1, True),
                6: (server_config['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/txt", ' + ad_dev + '}', 1, True),
                7: (server_config['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/balance", ' + ad_dev + '}', 1, True),
                8: (server_config['AD_PREF'] + "/switch/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/siren", "stat_off":"0", "stat_on":"1", "cmd_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "retain":"True", "pl_off":"3", "pl_on":"4", ' + ad_dev + '}', 1, True),
                9: (server_config['AD_PREF'] + "/switch/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/armed", "stat_off":"0", "stat_on":"1", "cmd_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "retain":"True", "pl_off":"00", "pl_on":"01", ' + ad_dev + '}', 1, True)
            }
            temp = general_msgs[int(id)]
            msgsAD.append(temp)

        if type == 'outputs' or type == 'groups':
            ad_dev = '"avty_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/connect/state", "device":{"identifiers":"' + str(imei) + '"}'
            try: ad_dev = ad_dev + ', "icon":"' + current_device[type][int(id)]['icon'] + '"'
            except: pass
            pl_off_ms = ""
            pl_on_ms = ""
            if type == 'outputs':
                pl_off_ms = "*#" + str(id+1) + "0"
                pl_on_ms = "*#" + str(id+1) + "9"
            if type == 'groups':
                pl_off_ms = "00" + str(id+1)
                pl_on_ms = "01" + str(id+1)
            temp = (server_config['AD_PREF'] + "/switch/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/state", "stat_off":"0", "stat_on":"1", "cmd_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "retain":"True", "pl_off":"' + pl_off_ms + '", "pl_on":"' + pl_on_ms + '", ' + ad_dev + '}', 1, True)
            try:
                if current_device[type][int(id)]['type'] == "lock":
                    temp = (server_config['AD_PREF'] + "/lock/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/state", "stat_locked":"1", "stat_unlocked":"0", "cmd_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "pl_unlk":"' + pl_off_ms + '", "pl_lock":"' + pl_on_ms + '", ' + ad_dev + '}', 1, True)
            except: pass
            msgsAD.append(temp)

        if type == 'adcs' or type == 'dallas' or type == 'counters' or type == 'address-sensors' or type == 'others':
            unit_of_m = {
                'adcs': "V",
                'dallas': "°C",
                'counters': " ",
                'address-sensors': "",
                'others': "",
            }
            ad_dev = '"avty_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/connect/state", "device":{"identifiers":"' + str(imei) + '"}'
            try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
            except: pass
            try: ad_dev = ad_dev + ', "icon":"' + current_device[type][int(id)]['icon'] + '"'
            except: pass
            temp = (server_config['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/value", "unit_of_meas":"' + unit_of_m[type] + '", ' + ad_dev + '}', 1, True)
            msgsAD.append(temp)

        if type == 'inputs':
            if ke == "alarm":
                device_type = "Охранный шлейф"
                ad_dev = '"avty_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/connect/state", "device":{ "identifiers":"' + str(imei) + '_In_' + str(id) + '", "name":"' + name + '", "manufacturer":"OKO", "model":"' + str(device_type) + '", "via_device":"' + str(imei) + '"}'
                try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
                except: pass
                name = name + " Тревога"
            if ke == "cut" or ke == "short":
                ad_dev = '"avty_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/connect/state", "device":{ "identifiers":"' + str(imei) + '_In_' + str(id) + '"}' + ', "device_class":"problem"'
                if ke == "cut": name = name + " Обрыв"
                if ke == "short": name = name + " КЗ"
            temp = (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke +'", "pl_off":"0", "pl_on":"1", ' + ad_dev + '}', 1, True)
            msgsAD.append(temp)

        try: radio_type = current_device[type][int(id)]['sensor_type']
        except: radio_type = ""
        if type == 'radios':
            if ke != "sensor_type":
                if ke == "alarm" or ke == "sos":
                    if radio_type == "event": radio_model = "Датчик события"
                    if radio_type == "magnet": radio_model = "Датчик открытия"
                    if radio_type == "temp": radio_model = "Датчик температуры"
                    if radio_type == "remote": radio_model = "Радио пульт"
                    ad_dev = '"avty_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/connect/state", "device":{ "identifiers":"' + str(imei) + '_R_' + str(id) + '", "name":"' + name + '", "manufacturer":"OKO", "model":"' + radio_model + '", "via_device":"' + str(imei) + '"}'
                    try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
                    except: pass
                else:
                    ad_dev = '"avty_t":"' + server_config['OKO_PREF'] + '/' + current_device['id'] + '/connect/state", "device":{ "identifiers":"' + str(imei) + '_R_' + str(id) + '"}'
                radio_msgs = {
                    "low_battery": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Батарея", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + ', "device_class":"battery"}', 1, True),
                    "tamper": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Вскрытие", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + ', "device_class":"safety"}', 1, True),
                    "alarm": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Тревога", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "test": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Тест", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + ', "device_class":"moving"}', 1, True),
                    "sos": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' SOS", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "home": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Дом", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "open": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Открыть", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "close": (server_config['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Закрыть", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "temp": (server_config['AD_PREF'] + "/sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' Темп", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "unit_of_meas":"°C", ' + ad_dev + ', "device_class":"temperature"}', 1, True)
                }
                temp = radio_msgs[ke]
                msgsAD.append(temp)
    else:
        UIC = str(server_config['OKO_PREF'] + '/' + current_device['id'])
        UID = str(server_config['OKO_PREF'] + '_' + current_device['id'] + '/' + str(type))
        UIB = str(server_config['OKO_PREF'] + '_' + current_device['id'])
        ad_dev = '"avty_t":"' + UIC + '/connect/state", "device":{ "identifiers":"' + str(imei) + '", "name":"' + current_device['name'] + '", "mf":"OKO", "mdl":"' + current_device['hw'] + '", "sw":"' + current_device['sw'] + '"}'

        code_msg= ""
        try:
            if 0 < int(current_device['code']) < 10000:
                code_msg = '"code":"' + str(current_device['code']) + '", '
        except: pass
        temp = (server_config['AD_PREF'] + "/alarm_control_panel/" + UID + "/config", '{"name":"' + current_device['name'] + '", "uniq_id":"' + UID + '", "stat_t":"' + UIC + '/mode", ' + code_msg + '"pl_disarm":"001,002,003", "pl_arm_away":"002,003,011", "pl_arm_home":"001,003,012", "pl_arm_nite":"001,002,013", "retain":"True", "cmd_t":"' + UIC + '/cmnd", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)
        ad_dev = '"avty_t":"' + UIC + '/connect/state", "device":{"identifiers":"' + str(imei) + '"}'
        temp = (server_config['AD_PREF'] + "/sensor/" + UIB + "/ip/config", '{"name":"IP", "uniq_id":"' + UIB + '/ip", "stat_t":"' + UIC + '/connect/ip", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)
        temp = (server_config['AD_PREF'] + "/sensor/" + UIB + "/port/config", '{"name":"Port", "uniq_id":"' + UIB + '/port", "stat_t":"' + UIC + '/connect/port", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)
        temp = (server_config['AD_PREF'] + "/sensor/" + UIB + "/time/config", '{"name":"Connected", "uniq_id":"' + UIB + '/time", "stat_t":"' + UIC + '/connect/time", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)

def make_msg_status(imei, type, id, ke, value):
    current_device = search_device_config(imei)
    url = server_config['OKO_PREF'] + '/' + str(current_device['id']) + '/' + str(type)
    if type != 'mode':
         url = url + '/' + str(id+1) + '/' + str(ke)
    temp = (url, value, 1, True)
    msgsST.append(temp)

def compare_device_status(oldStatus, newStatus):
    current_device = search_device_config(newStatus['imei'])
    ddiff = DeepDiff(oldStatus, newStatus, ignore_order=False, verbose_level=2)
    #print("Diff is ")
    #pprint(ddiff)#
    #pprint (oldStatus)
    #pprint (newStatus)
    if ddiff:

        for key, value in ddiff.items():
            if key == 'values_changed':
                for key, value in value.items():
                    work_with_value (newStatus['imei'], "U", key, value['new_value'])
            elif key == 'dictionary_item_added':
                for key, value in value.items():
                    #print (newStatus['imei'], "A", key, value)
                    work_with_value (newStatus['imei'], "A", key, value)
                write_JSON_file(devices_config, './config/devices.json')
            elif key == 'dictionary_item_removed':
                for key, value in value.items():
                    work_with_value (newStatus['imei'], "D", key, value)
            else:
                logging.error("[" + str(current_device['id']) + "] Error! No ddiff values")
        #pprint(msgsAD)
        #print(server_config['MQTT_IP'])


        #print (topic)
#ттут сильно надо пробатвь!
        try:
            if msgsAD != [ ]:
                publish.multiple(msgsAD, hostname=server_config['MQTT_IP'], port=server_config['MQTT_PORT'], client_id='oko2mqtt', auth={'username':server_config['MQTT_USER'], 'password':server_config['MQTT_PASSWORD']})
                logging.info("[" + str(current_device['id']) + "] Publish " + str(len(msgsAD)) + " autoDiscovery messages")
                #logging.debug("[" + str(current_device['id']) + "] " + str(len(msgsAD)) + " autoDiscovery")
        except:
            pass
        #try:
        #if msgsST != [ ]:
        #
        #msg = {'topic':topic, 'payload':'offline', 'qos':1}
        #print (will)

        #topic = server_config['OKO_PREF'] + '/' + str(current_device['id']) + '/' + "connect/state"
        temp = (server_config['OKO_PREF'] + '/' + str(current_device['id']) + '/' + "connect/state", 'online', 1)
        msgsST.append(temp)
        publish.multiple(msgsST, hostname=server_config['MQTT_IP'], port=server_config['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':server_config['MQTT_USER'], 'password':server_config['MQTT_PASSWORD']})#will = {'topic':topic, 'payload':'offline', 'qos':1},
        #publish.single(topic, payload='offline', qos=1, hostname=server_config['MQTT_IP'], port=server_config['MQTT_PORT'], client_id='oko2mqtt', will = {'topic':topic, 'payload':'offline', 'qos':1}, auth = {'username':server_config['MQTT_USER'], 'password':server_config['MQTT_PASSWORD']})
        #logging.info("[" + str(current_device['id']) + "] Publish status messages")
        logging.info("[" + str(current_device['id']) + "] Publish " + str(len(msgsST)) + " status messages")
    #except:
        #    pass
        #msgsAD = [{}]

        #pprint(msgsAD)
        return

def handle_socket_client(client_list, conn, address):
    logging.warning("New connection from " + str(address))
    newConn = True
    while 1:
        def subscribe_cmnd_topic(id, pin):
            def on_cmnd_receive(client, userdata, message):
                cmd = message.payload.decode()
                msg = "COMMAND:" + pin + cmd + ",70;"
                msg = msg.encode()
                try:
                    conn.send(msg)
                    logging.info("[" + str(id) + "] Cmnd send")
                    logging.debug("[" + str(id) + "] Cmnd " + str(cmd))
                except:
                    logging.info("[" + str(id) + "] Cmnd send ERROR")
                    logging.debug("[" + str(id) + "] Cmnd " + str(cmd))
                    pass

            logging.info("[" + str(id) + "] Subscribe on cmnd topic")
            msgsST.clear()
            topic = server_config['OKO_PREF'] + '/' + str(id) + '/' + "connect/"
            temp = (topic + "state", 'online', 1, True)
            msgsST.append(temp)
            temp = (topic + "ip", str(address[0]), 1, True)
            msgsST.append(temp)
            temp = (topic + "port", str(address[1]), 1, True)
            msgsST.append(temp)
            temp = (topic + "time", str(datetime.today().strftime("%H:%M:%S %d-%m-%Y")), 1, True)
            msgsST.append(temp)
            topic = topic + "state"
            publish.multiple(msgsST, hostname=server_config['MQTT_IP'], port=server_config['MQTT_PORT'], client_id='oko2mqtt', will = {'topic':topic, 'payload':'offline', 'qos':1}, auth = {'username':server_config['MQTT_USER'], 'password':server_config['MQTT_PASSWORD']})
            logging.info("[" + str(id) + "] Publish connect topic")
            subscribe.callback(on_cmnd_receive, server_config['OKO_PREF'] + '/' + str(id) + '/cmnd', hostname=server_config['MQTT_IP'], port=server_config['MQTT_PORT'], client_id='oko2mqtt', will = {'topic':topic, 'payload':'offline', 'qos':1}, auth = {'username':server_config['MQTT_USER'], 'password':server_config['MQTT_PASSWORD']})

        try:
            msg = conn.recv(1024)
        except:
            logging.debug("[" + str(devId) + "] Cannot recieve data")
            break
        if not msg:
            logging.debug("[" + str(devId) + "] No data")
            break

        msgsAD.clear()
        msgsST.clear()

        devId, devPin = scan_msg(msg.decode())

        if newConn and devId and devPin :
            newConn = False
            proc = Process(target=subscribe_cmnd_topic, args=(devId,devPin))
            proc.start()



    proc.terminate()
    publish.single(server_config['OKO_PREF'] + '/' + str(devId) + '/' + "connect/state", payload='offline', qos=1, hostname=server_config['MQTT_IP'], port=server_config['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':server_config['MQTT_USER'], 'password':server_config['MQTT_PASSWORD']})
    try: conn.shutdown(socket.SHUT_RDWR)
    except: pass
    try: conn.close()
    except: pass
    logging.warning("[" + str(devId) + "] Socket closed")

def start_socket_server(client_list):
    logging.warning("Starting server at " + str(server_config['SOCKET_IP']) + " on " + str(server_config['SOCKET_PORT']))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((server_config['SOCKET_IP'], server_config['SOCKET_PORT']))
    s.listen(server_config['SOCKET_LISTEN'])
    while True:
        (conn, address) = s.accept()
        conn.settimeout(server_config['SOCKET_TIMEOUT'])
        t = Thread(target=handle_socket_client, args=(client_list, conn, address), daemon = True)
        t.start()

def main():
    coloredlogs.DEFAULT_LOG_LEVEL = server_config['LOG_LEVEL']
    coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'white'}, 'levelname': {'bold': True, 'color': 'black'}, 'threadName': {'color': 'magenta'}, 'process': {'color': 'yellow'}}
    coloredlogs.install(fmt='%(asctime)s.%(msecs)03d  %(levelname)-8s %(threadName)-11s %(process)d %(message)s', datefmt='%H:%M:%S')
    client_list = dict()
    try: start_socket_server(client_list)
    except KeyboardInterrupt: logging.critical("Keyboard interrupt")


msgsAD = []
msgsST = []
devices_status = json.loads('[]')


server_config = read_JSON_file('./config/server.json')
if server_config == False:
    server_config = {
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
      "LOG_LEVEL": 30
    }
    write_JSON_file(server_config, './config/server.json')
    logging.warning("Default server config saved")

msg_codes = read_JSON_file('./dev/msg_codes.json')

devices_config = read_JSON_file('./config/devices.json')
if devices_config == False:
    devices_config = json.loads('[]')
    write_JSON_file(devices_config, './config/devices.json')
    logging.warning("Clear devices config saved")

if __name__ == '__main__':
    main()
