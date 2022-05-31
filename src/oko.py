# -*- coding: utf-8 -*-
import logging, json, time

from src import etc, cfg, mqtt


import paho.mqtt.publish as publish

from datetime import datetime

import coloredlogs
from bitstring import BitArray
from deepdiff import DeepDiff
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe

devices_status = json.loads('[]')

msgsAD = []
msgsST = []
msgsCN = []

def check_devices_msg():
    logging.info(f"Check devices last msg time")
    now = time.time()
    for deviceConfig in cfg.devices:
        for deviceStatus in devices_status:
            if deviceStatus['imei'] == deviceConfig['imei']:
                if now - float(deviceStatus['time']) > cfg.server['SOCKET_TIMEOUT']:
                    logging.error(f"[{deviceConfig['id']}] No msgs from {deviceConfig['name']} more than {cfg.server['SOCKET_TIMEOUT']} sec")
                    mqtt.pubConn(deviceConfig['id'], False)
                    makeExConnMsgs(deviceConfig, False)
                    
                else:
                    logging.info(f"[{deviceConfig['id']}] Connect with {deviceConfig['name']} - OK")

                break
        else:
            logging.error(f"[{deviceConfig['id']}] Not any msgs from {deviceConfig['name']} yet")
            mqtt.pubConn(deviceConfig['id'], False)
            makeExConnMsgs(deviceConfig, False)


def makeExConnMsgs(deviceConfig, state):
    ex_id = 1
    while ex_id < 5:
        clear = True
        ex_txt = 'ex' + str(ex_id) + '_in'
        for single in deviceConfig[ex_txt]:
            if single:
                clear = False
        ex_txt = 'ex' + str(ex_id) + '_out'
        for single in deviceConfig[ex_txt]:
            if single:
                clear = False
        if clear == False:
            mqtt.pubConnEx(deviceConfig['id'], ex_id, False)
        ex_id += 1


def scan_msg(msgData):

    def parse_msg_to_json(msg):

        if len(msg) > 100:
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

                def cut2bits(cut):
                    bits = byte2bits(bytes.fromhex(cut)[1])
                    i = 0
                    obj = [{},{},{},{},{},{},{},{}]
                    while i < 8:
                        obj[i]['state'] = str(int(bits[7-i]))
                        i += 1
                    return obj

                def cut2mode(cut):
                    bytess = bytes.fromhex(cut)[1]
                    switcher = {
                         0:'disarmed',
                         1:'armed_away',
                         2:'armed_home',
                         4:'armed_night'
                    }
                    return switcher.get(bytess, "unknown")


                def cut2inputs(cut):

                    in_alarm = byte2bits(bytes.fromhex(cut)[1])
                    in_cut = byte2bits(bytes.fromhex(cut)[2])
                    in_short = byte2bits(bytes.fromhex(cut)[3])

                    obj = [{},{},{},{},{},{},{},{}]
                    i = 0
                    while i < 8:
                        if i < len(in_alarm):
                            obj[i]['alarm'] = str(int(in_alarm[len(in_alarm)-1-i]))
                        else:
                            obj[i]['alarm'] = 0

                        if i < len(in_cut):
                            obj[i]['cut'] = str(int(in_cut[len(in_cut)-1-i]))
                        else:
                            obj[i]['cut'] = 0

                        if i < len(in_short):
                            obj[i]['short'] = str(int(in_short[len(in_short)-1-i]))
                        else:
                            obj[i]['short'] = 0
                        i += 1
                    return obj

                def cut2dallas(cut):
                    obj = [{},{},{},{},{},{},{},{}]
                    i = 0
                    while i < 8:
                        if byte2temp(bytes.fromhex(cut)[i]):
                            obj[i]['value'] = str(byte2temp(bytes.fromhex(cut)[i]))
                        i += 1
                    return obj

                def cut2adcs(cut):
                    obj = [{},{},{},{},{}]
                    i = 0
                    while i < 5:
                        obj[i]['value'] = str(round(bytes2adc(cut[(i * 4):(i * 4 + 4)]),1))
                        i += 1
                    return obj

                def cut2radios(cut):
                    obj = [{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]
                    i = 0
                    while i < 16:
                        obj[i] = bytes2radio(cut[(i * 4):(i * 4 + 4)])
                        i += 1
                    return obj

                def cuts2counters(cuts, start_cut_id):
                    obj = [{},{},{},{},{},{},{},{}]
                    i = 0
                    while i < 8:
                        if cuts[start_cut_id+i]: obj[i]['count'] = str(int(cuts[start_cut_id+i]))
                        i += 1
                    return obj

                def cut2general(cuts):
                    obj = [{},{},{},{},{},{},{},{},{},{}]
                    general_state = byte2bits(int(cuts[3][0:2], 16))
                    obj[0]['tamper'] = str(int(general_state[3]))
                    obj[1]['power'] = str(int(general_state[5]))
                    obj[2]['bat12v'] = str(int(general_state[4]))
                    obj[3]['bat5v'] = str(int(general_state[2]))
                    obj[4]['gsm'] = str(-113 + (int(cuts[5], 16) * 2)) #to dBm
                    obj[5]['code'] = str(int(cuts[1], 16))
                    obj[6]['txt'] = etc.msg_codes[int(cuts[1], 16)]
                    obj[7]['balance'] = cuts[11]
                    obj[8]['siren'] = str(int(bool(byte2bits(bytes.fromhex(cuts[4])[0])[7])))
                    obj[9]['armed'] = str(int(bool(bytes.fromhex(cuts[2])[1])))
                    return obj

                def cuts2address(cuts, start_cut_id):
                    obj = [{},{},{},{},{},{},{},{}]
                    i = 0
                    while i < 8:
                        if cuts[start_cut_id+i]: obj[i]['value'] = cuts[start_cut_id+i]
                        i += 1
                    return obj

                def cuts2others(cuts):
                    obj = [{},{},{},{},{},{},{},{}]
                    if cuts[28] or cuts[29]:
                        obj[6]['type'] = cuts[28]
                        obj[7]['value'] = cuts[29]
                    #if cuts[30]: obj[1]['value'] = cuts[30] #ex1
                    #if cuts[31]: obj[2]['value'] = cuts[31] #ex2
                    #if cuts[32]: obj[3]['value'] = cuts[32] #ex3
                    #if cuts[33]: obj[4]['value'] = cuts[33] #ex4
                    if cuts[34]: obj[0]['value'] = cuts[34] #ex0
                    if cuts[35]: obj[5]['value'] = cuts[35] #radio_sockets
                    return obj
                
                def makeExAvblMsg(imei, ex_id, state):
                    for device_config in cfg.devices_config:
                        if device_config['imei'] == imei:
                            ex_txt = 'ex' + str(ex_id) + '_in'
                            for single in device_config[ex_txt]:
                                if single:
                                    #logging.error(f"{ex_txt}")
                                    make_msg_connect(device_config['id'], 'ex' + str(ex_id), state)
                            ex_txt = 'ex' + str(ex_id) + '_out'
                            for single in device_config[ex_txt]:
                                if single:
                                    #logging.error(f"{ex_txt}")
                                    make_msg_connect(device_config['id'], 'ex' + str(ex_id), state)
                            #mqtt.pubConnEx(device_config['id'], ex_id, state)

                def cut2ex(cut, imei, ex_id):
                    obj_in = [{},{},{},{},{},{},{},{}]
                    obj_out = [{},{},{},{},{},{},{},{}]
                    if cut:
                        state = byte2bits(int(cut[0:2], 16))

                        board_type = str(int(state[6])) + str(int(state[7]))
                        logging.debug(f"ex board type {board_type}")

                        #!! input_2_zone not work !! on OKO-EX v.4.2
                        #input_2_zone = str(int(state[2])) + str(int(state[3])) + str(int(state[4])) + str(int(state[5]))
                        #logging.warning(input_2_zone)

                        #input 5..8 state
                        state = byte2bits(int(cut[2:4], 16))
                        i = 0
                        while i < 4:
                            if (board_type == "00" or board_type == "10"): #tried if ((board_type == "00" and input_2_zone[3-i] == "1") or board_type == "10"): but input_2_zone not work
                                cur = str(int(state[len(state)-1-i*2-1])) + str(int(state[len(state)-1-i*2]))
                                if cur == "00":
                                    obj_in[i+4]['alarm'] = '0'
                                    obj_in[i+4]['cut'] = '0'
                                    obj_in[i+4]['short'] = '0'
                                elif cur == "01":
                                    obj_in[i+4]['alarm'] = '1'
                                    obj_in[i+4]['cut'] = '0'
                                    obj_in[i+4]['short'] = '0'
                                elif cur == "10":
                                    obj_in[i+4]['alarm'] = '1'
                                    obj_in[i+4]['cut'] = '0'
                                    obj_in[i+4]['short'] = '1'
                                elif cur == "11":
                                    obj_in[i+4]['alarm'] = '1'
                                    obj_in[i+4]['cut'] = '1'
                                    obj_in[i+4]['short'] = '0'
                            i += 1

                        #input 1..4 state
                        state = byte2bits(int(cut[4:6], 16))
                        i = 0
                        while i < 4:
                            if (board_type == "00" or board_type == "10"):
                                cur = str(int(state[len(state)-1-i*2-1])) + str(int(state[len(state)-1-i*2]))
                                if cur == "00":
                                    obj_in[i]['alarm'] = '0'
                                    obj_in[i]['cut'] = '0'
                                    obj_in[i]['short'] = '0'
                                elif cur == "01":
                                    obj_in[i]['alarm'] = '1'
                                    obj_in[i]['cut'] = '0'
                                    obj_in[i]['short'] = '0'
                                elif cur == "10":
                                    obj_in[i]['alarm'] = '1'
                                    obj_in[i]['cut'] = '0'
                                    obj_in[i]['short'] = '1'
                                elif cur == "11":
                                    obj_in[i]['alarm'] = '1'
                                    obj_in[i]['cut'] = '1'
                                    obj_in[i]['short'] = '0'   
                            i += 1

                        #outputs state
                        state = byte2bits(int(cut[6:8], 16))
                        i = 0
                        while i < 8:
                            if ((board_type == "00" and (i < 4)) or board_type == "01"):
                                obj_out[i]['state'] = str(int(state[len(state)-1-i]))
                            i += 1
                        makeExAvblMsg(imei, ex_id, 1)
                    else:
                        makeExAvblMsg(imei, ex_id, 0)
                    return obj_in, obj_out


                dev_state = etc.read_JSON_file('./dev/clean.json')
                dev_state['imei'] = cuts[0]
                dev_state['hw'] = cuts[10]
                dev_state['sw'] = cuts[9]
                dev_state['mode'] = cut2mode(cuts[2])
                dev_state['general'] = cut2general(cuts)
                dev_state['groups'] = cut2bits(cuts[2])

                dev_state['inputs'] = cut2inputs(cuts[3])
                dev_state['outputs'] = cut2bits(cuts[4])
                dev_state['dallas'] = cut2dallas(cuts[6])
                dev_state['radios'] = cut2radios(cuts[7])
                dev_state['adcs'] = cut2adcs(cuts[8])

                dev_state['counters'] = cuts2counters(cuts, 12)
                dev_state['address-sensors'] = cuts2address(cuts, 20)

                dev_state['ex1_in'], dev_state['ex1_out'] = cut2ex(cuts[30], cuts[0], 1)
                dev_state['ex2_in'], dev_state['ex2_out'] = cut2ex(cuts[31], cuts[0], 2)
                dev_state['ex3_in'], dev_state['ex3_out'] = cut2ex(cuts[32], cuts[0], 3)
                dev_state['ex4_in'], dev_state['ex4_out'] = cut2ex(cuts[33], cuts[0], 4)

                dev_state['others'] = cuts2others(cuts)

                logging.debug(dev_state)
                return dev_state
            else:
                return None
        else:
            return None

    def update_device_config_value(key, old, new):
        for device in cfg.devices:
            if device[key] == old:
                device[key] = str(new)
                return True

    newMsg = parse_msg_to_json(msgData)
    if newMsg:
        device_config = cfg.search_device(newMsg['imei'])
        if device_config:
            try:
                publish.single(cfg.server['OKO_PREF'] + '/' + str(device_config['id']) + '/' + "cmnd", payload='', qos=1, retain=1, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']})
            except:
                logging.error("Failed to connect to MQTT server")
            if (device_config['sw'] != newMsg['sw']):
                logging.warning("[" + str(device_config['id']) + "] New firmware [" + newMsg['sw'] + " vs " + device_config['sw'] + "] Check all then update config")

            statusInit = True
            for device_status in devices_status:
                if device_status['imei'] == newMsg['imei']:
                    statusInit = False
                    device_status['time'] = time.time()
                    logging.info('[' + device_config['id'] + '] Message recived')
                    compare_device_status(device_status, newMsg)
                    return device_config['id'], device_config['pin']

            if statusInit:
                devices_status.append(etc.read_JSON_file('./dev/clean.json'))
                for device_status in devices_status:
                    if device_status['imei'] == "0":
                        device_status['imei'] = newMsg['imei']
                        # to do down. this way error ?
                        #device_status['id'] = device_config['id']
                        #device_status['name'] = device_config['name']
                        device_status['time'] = time.time()
                        logging.info('[' + device_config['id'] + '] Device config found')
                        compare_device_status(device_status, newMsg)
                        return device_config['id'], device_config['pin']


        else:
            cfg.devices.append(etc.read_JSON_file('./dev/clean.json'))
            update_device_config_value('imei', '0', newMsg['imei'])
            update_device_config_value('name', 'Unknown', newMsg['hw'] + ' ' + newMsg['imei'][-4:])
            update_device_config_value('id', 'unk', 'oko_' + newMsg['imei'][-6:])
            update_device_config_value('hw', '0', newMsg['hw'])
            update_device_config_value('sw', '0', newMsg['sw'])
            logging.warning('New device, type ' + newMsg['hw'] + ' v' + newMsg['sw'] + ' with IMEI ' + newMsg['imei'])
            etc.write_JSON_file(cfg.devices, './config/devices.json')
            return scan_msg(msgData)
    else: 
        return None, None


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
                 0: 'Tamper',
                 1: 'Power supply',
                 2: '12V battery',
                 3: '5V battery',
                 4: 'GSM level',
                 5: 'Status code',
                 6: 'Status',
                 7: 'Balance',
                 8: 'Siren',
                 9: 'Security mode'
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
            if int(id) < 5:
                return json.loads('{ "name":"' + str(name.get(int(id), '')) + '","class":"' + str(icon.get(int(id), '')) + '" }')
            else:
                return json.loads('{ "name":"' + str(name.get(int(id), '')) + '","icon":"' + str(icon.get(int(id), '')) + '" }')

        elif type == "inputs":
            if ke == "alarm":
                if int(id) < 4:
                    return json.loads('{ "name":"Input '+str(id+1)+'","class":"window","short":true,"cut":true }')
                else:
                    return json.loads('{ "name":"","class":"","short":false,"cut":false }')
            else:
                return False

        elif type == "groups":
            if 2 < int(id) < 6:
                return json.loads('{ "name":"Group '+str(id+1)+'","icon":"mdi:group" }')
            else:
                return json.loads('{ "name":"","icon":"" }')

        elif type == "outputs":
            if 0 < int(id) < 3:
                return json.loads('{ "name":"Output '+str(id+1)+'","icon":"mdi:flash" }')
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
                return json.loads('{ "name":"Radio '+str(id+1)+'","class":"window","sensor_type":"'+value+'" }')
            else:
                return False

        elif type == "others":
            return json.loads('{ "name":"EX '+str(id)+'","icon":"mdi:file-question" }')

        elif type == "counters":
            return json.loads('{ "name":"Counter '+str(id+1)+'","icon":"mdi:numeric" }')

        elif type[-2:] == "in":
            if ke == "alarm":
                if int(id) % 2 == 0:
                    return json.loads('{ "name":"'+str(type)+' '+str(id+1)+'","class":"window","short":true,"cut":true }')
                else:
                    return json.loads('{ "name":"'+str(type)+' '+str(id+1)+'","class":"door","short":true,"cut":true }')
            else:
                return False

            #return json.loads('{ "name":"'+str(type)+' '+str(id+1)+'","icon":"mdi:security-network" }')

        elif type[-3:] == "out":
            return json.loads('{ "name":"'+str(type)+' '+str(id+1)+'","icon":"mdi:flash" }')

        elif type[:-1] == "sockets_bkl":
            return json.loads('{ "name":"'+str(type)+' socket '+str(id+1)+'","icon":"mdi:radio-tower" }')

        else:
            return json.loads('{ "name":"" }')

    def update_device_status_value(imei, type, id, ke, value):
        for device_status in devices_status:
            if device_status['imei'] == str(imei):
                if type == 'mode':
                    device_status[type] = value
                else:
                    device_status[type][int(id)][ke] = value
                #if value:
                make_msg_status(imei, type, id, ke, value)

    def delete_device_status_value(imei, type, id):
        logging.debug(f"del {imei} - {type} - {id}")
        for device_status in devices_status:
            if device_status['imei'] == str(imei):
                #logging.warning(f"{device_status[type]}")
                if type == 'mode':
                    device_status[type] = {}
                elif type == 'time':
                    break
                else:
                    device_status[type][int(id)] = {}
                        

    
    logging.debug(f"work_with_value {imei}, {action}, {key}, {value}")
    type, id, ke = key_extract_from_string(key)
    if (type != 'sw') and (type != 'hw') and (type != 'imei'):
        if action == "A":
            for device in cfg.devices:
                if device['imei'] == str(imei):
                    if type == 'mode':
                        update_device_status_value(imei, type, id, ke, value)
                        if cfg.server['AD_ENBL'] == True: make_msg_discovery(imei, type, id, ke)
                    else:
                        if str(device[type][int(id)]) == '{}':
                            beta = init_device_sensor(type, id, ke, value)
                            if beta != False:
                                device[type][int(id)] = beta
                        try:
                            if str(device[type][int(id)]['name']):
                                if type == 'inputs' or type[-2:] == 'in':
                                    if (ke == "cut") or (ke == "short"):
                                        if bool(device[type][int(id)][str(ke)]) == False:
                                            update_device_status_value(imei, type, id, ke, value)
                                            break
                                update_device_status_value(imei, type, id, ke, value)
                                if cfg.server['AD_ENBL'] == True: make_msg_discovery(imei, type, id, ke)
                        except:
                            pass
                    #if type[:2] == 'ex':
                        #if type[-2:] == 'in':
                        #    if (ke == "cut") or (ke == "short"):
                        #        break
                        #mqtt.pubConnEx(device['id'], type[2:3], 1)
                        #make_msg_connect(imei, type, 1)

        if action == "U":
            for device in cfg.devices:
                if device['imei'] == str(imei):
                    if type == 'mode':
                        update_device_status_value(imei, type, id, ke, value)
                    else:
                        if device[type][int(id)]['name']:
                             update_device_status_value(imei, type, id, ke, value)

        if action == "D":
            pass
            #for device in cfg.devices:
            #    if device['imei'] == str(imei):
            #        delete_device_status_value(imei, type, id)
            #        if type[:2] == 'ex':
            #            if type[-2:] == 'in':
            #                if (ke == "cut") or (ke == "short"):
            #                    break
                        #mqtt.pubConnEx(device['id'], type[2:3], 0)
                        #make_msg_connect(imei, type, 0)

            #for device in cfg.devices:
            #    if device['imei'] == str(imei):
            #        if type == 'mode':
            #                update_device_status_value(imei, type, id, ke, 'NaN')
            #        elif type == 'time':
            #            pass
            #        else:
            #            if device[type][int(id)]['name']:
            #                update_device_status_value(imei, type, id, ke, 'NaN')

def make_msg_discovery(imei, type, id, ke):
    current_device = cfg.search_device(imei)
    if type != 'mode':
        UID = str(cfg.server['OKO_PREF'] + '_' + current_device['id'] + '/' + str(type) + '_' + str(id+1))
        UID2 = str(cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/' + str(type) + '/' + str(id+1))
        name = current_device[type][int(id)]['name']

        if type == 'general':
            ad_dev = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/main", "device":{"identifiers":"' + str(imei) + '"}'
            try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
            except: pass
            try: ad_dev = ad_dev + ', "icon":"' + current_device[type][int(id)]['icon'] + '"'
            except: pass
            general_msgs = {
                0: (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/tamper", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                1: (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/power", "pl_off":"0", "pl_on":"1", ' + ad_dev + '}', 1, True),
                2: (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/bat12v", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                3: (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/bat5v", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                4: (cfg.server['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/gsm", "unit_of_meas":"dBm", ' + ad_dev + '}', 1, True),
                5: (cfg.server['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/code", "unit_of_meas":" ", ' + ad_dev + '}', 1, True),
                6: (cfg.server['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/txt", ' + ad_dev + '}', 1, True),
                7: (cfg.server['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/balance", ' + ad_dev + '}', 1, True),
                8: (cfg.server['AD_PREF'] + "/switch/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/siren", "stat_off":"0", "stat_on":"1", "cmd_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "retain":"True", "pl_off":"3", "pl_on":"4", ' + ad_dev + '}', 1, True),
                9: (cfg.server['AD_PREF'] + "/switch/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/armed", "stat_off":"0", "stat_on":"1", "cmd_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "retain":"True", "pl_off":"00", "pl_on":"01", ' + ad_dev + '}', 1, True)
            }
            temp = general_msgs[int(id)]
            msgsAD.append(temp)

        if type == 'outputs' or type == 'groups' or type[-3:] == 'out':

            if type[-3:] == 'out':
                device_str = str(imei) + '_Ex_' + str(type[2:3])
                type_txt = type[:3]
            else:
                device_str = str(imei)
                #type_txt = type

            #/etc/ex2/conn
            if id == 0 and type[-3:] == 'out':
                device_type = "EX board"
                device_txt = '"device":{ "identifiers":"' + str(device_str) + '", "name":"' + type_txt + '", "manufacturer":"OKO", "model":"' + str(device_type) + '", "via_device":"' + str(imei) + '"}'
            else:
                device_txt = '"device":{ "identifiers":"' + str(device_str) + '"}'

            if type[-3:] == 'out':
                ad_dev = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/' + type[:3] + '", ' + device_txt
            else:
                ad_dev = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/main", ' + device_txt
            
            try: ad_dev = ad_dev + ', "icon":"' + current_device[type][int(id)]['icon'] + '"'
            except: pass

            pl_off_ms = ""
            pl_on_ms = ""
            if type == 'outputs':
                pl_off_ms = "*#" + str(id+1) + "0"
                pl_on_ms = "*#" + str(id+1) + "9"
            elif type == 'groups':
                pl_off_ms = "00" + str(id+1)
                pl_on_ms = "01" + str(id+1)
            elif type[-3:] == 'out':
                pl_off_ms = "*" + str(type[2:3])+ "#" + str(id+1) + "0"
                pl_on_ms = "*" + str(type[2:3])+ "#" + str(id+1) + "9"

            temp = (cfg.server['AD_PREF'] + "/switch/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/state", "stat_off":"0", "stat_on":"1", "cmd_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "retain":"True", "pl_off":"' + pl_off_ms + '", "pl_on":"' + pl_on_ms + '", ' + ad_dev + '}', 1, True)
            try:
                if current_device[type][int(id)]['type'] == "lock":
                    temp = (cfg.server['AD_PREF'] + "/lock/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/state", "stat_locked":"1", "stat_unlocked":"0", "cmd_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/cmnd", "pl_unlk":"' + pl_off_ms + '", "pl_lock":"' + pl_on_ms + '", ' + ad_dev + '}', 1, True)
            except: pass
            msgsAD.append(temp)

        if type == 'adcs' or type == 'dallas' or type == 'address-sensors' or type == 'others':
            unit_of_m = {
                'adcs': "V",
                'dallas': "°C",
                'address-sensors': "",
                'others': "",
            }
            ad_dev = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/main", "device":{"identifiers":"' + str(imei) + '"}'
            try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
            except: pass
            try: ad_dev = ad_dev + ', "icon":"' + current_device[type][int(id)]['icon'] + '"'
            except: pass
            temp = (cfg.server['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/value", "unit_of_meas":"' + unit_of_m[type] + '", ' + ad_dev + '}', 1, True)
            msgsAD.append(temp)

        if type == 'counters':
            unit_of_m = {
                'counters': " ",
            }
            ad_dev = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/main", "device":{"identifiers":"' + str(imei) + '"}'
            try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
            except: pass
            try: ad_dev = ad_dev + ', "icon":"' + current_device[type][int(id)]['icon'] + '"'
            except: pass
            temp = (cfg.server['AD_PREF'] + "/sensor/" + UID + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + '", "stat_t":"' + UID2 + '/count", "unit_of_meas":"' + unit_of_m[type] + '", ' + ad_dev + '}', 1, True)
            msgsAD.append(temp)

        if type == 'inputs' or type[-2:] == 'in':
            if type[-2:] == 'in':
                device_str = str(imei) + '_Ex_' + str(type[2:3])
                type_txt = type[:3]
            else :
                device_str = str(imei)# + '_Inputs'
                #type_txt = type

            #{"name":"ex1_in 4 Short", "uniq_id":"okko_test_oko_523343/ex1_in_4_short", "stat_t":"okko_test/oko_523343/ex1_in/4/short", "pl_off":"0", "pl_on":"1", "avty_t":"okko_test/oko_523343/etc/ex1/conn", "device":{ "identifiers":"861230040523343_Ex_1"}, "device_class":"problem"}

            #{"name":"ex2_out 2", "uniq_id":"okko_test_oko_523343/ex2_out_2", "stat_t":"okko_test/oko_523343/ex2_out/2/state", "stat_off":"0", "stat_on":"1", "cmd_t":"okko_test/oko_523343/cmnd", "retain":"True", "pl_off":"*2#20", "pl_on":"*2#29", "avty_t":"okko_test/oko_523343/etc/ex2/conn", "device":{ "identifiers":"861230040523343_Ex_2"}, "icon":"mdi:flash"}
            if id == 0 and ke == "alarm" and type[-2:] == 'in':
                device_type = "EX board"
                device_txt = '"device":{ "identifiers":"' + str(device_str) + '", "name":"' + type_txt + '", "manufacturer":"OKO", "model":"' + str(device_type) + '", "via_device":"' + str(imei) + '"}'
            else:
                device_txt = '"device":{ "identifiers":"' + str(device_str) + '"}'


            if type[-2:] == 'in':
                ad_dev_txt = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/' + type[:3] + '", ' 
            else:
                ad_dev_txt = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/main", '

            if ke == "alarm":
                #device_type = "Security loop"
                ad_dev = ad_dev_txt + device_txt
                try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
                except: pass
                name = name + " Alarm"
            if ke == "cut" or ke == "short":
                ad_dev = ad_dev_txt + device_txt + ', "device_class":"problem"'
                if ke == "alarm": name = name + " Alarm"
                if ke == "cut": name = name + " Cut"
                if ke == "short": name = name + " Short"
            temp = (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + '", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke +'", "pl_off":"0", "pl_on":"1", ' + ad_dev + '}', 1, True)
            msgsAD.append(temp)

        try: radio_type = current_device[type][int(id)]['sensor_type']
        except: radio_type = ""
        if type == 'radios':
            if ke != "sensor_type":
                if ke == "alarm" or ke == "sos":
                    if radio_type == "event": radio_model = "Event sensor"
                    if radio_type == "magnet": radio_model = "Opening sensor"
                    if radio_type == "temp": radio_model = "Temperature sensor"
                    if radio_type == "remote": radio_model = "Remote control"
                    ad_dev = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/main", "device":{ "identifiers":"' + str(imei) + '_R_' + str(id) + '", "name":"' + name + '", "manufacturer":"OKO", "model":"' + radio_model + '", "via_device":"' + str(imei) + '"}'
                    try: ad_dev = ad_dev + ', "device_class":"' + current_device[type][int(id)]['class'] + '"'
                    except: pass
                else:
                    ad_dev = '"avty_t":"' + cfg.server['OKO_PREF'] + '/' + current_device['id'] + '/connect/main", "device":{ "identifiers":"' + str(imei) + '_R_' + str(id) + '"}'
                radio_msgs = {
                    "low_battery": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' battery", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + ', "device_class":"battery"}', 1, True),
                    "tamper": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' tamper", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + ', "device_class":"safety"}', 1, True),
                    "alarm": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' alarm", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "test": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' test", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + ', "device_class":"moving"}', 1, True),
                    "sos": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' SOS", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "home": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' home", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "open": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' open", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "close": (cfg.server['AD_PREF'] + "/binary_sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' close", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "pl_off":"1", "pl_on":"0", ' + ad_dev + '}', 1, True),
                    "temp": (cfg.server['AD_PREF'] + "/sensor/" + UID + "_" + ke + "/config", '{"name":"' + name + ' temp", "uniq_id":"' + UID + "_" + ke + '", "stat_t":"' + UID2 + '/' + ke + '", "unit_of_meas":"°C", ' + ad_dev + ', "device_class":"temperature"}', 1, True)
                }
                temp = radio_msgs[ke]
                msgsAD.append(temp)
    else:
        UIC = str(cfg.server['OKO_PREF'] + '/' + current_device['id'])
        UID = str(cfg.server['OKO_PREF'] + '_' + current_device['id'] + '/' + str(type))
        UIB = str(cfg.server['OKO_PREF'] + '_' + current_device['id'])
        ad_dev = '"avty_t":"' + UIC + '/connect/main", "device":{ "identifiers":"' + str(imei) + '", "name":"' + current_device['name'] + '", "mf":"OKO", "mdl":"' + current_device['hw'] + '", "sw":"' + current_device['sw'] + '"}'

        code_msg= ""
        try:
            if 0 < int(current_device['code']) < 10000:
                code_msg = '"code":"' + str(current_device['code']) + '", '
        except: pass
        temp = (cfg.server['AD_PREF'] + "/alarm_control_panel/" + UID + "/config", '{"name":"' + current_device['name'] + '", "uniq_id":"' + UID + '", "stat_t":"' + UIC + '/mode", ' + code_msg + '"pl_disarm":"001,002,003", "pl_arm_away":"002,003,011", "pl_arm_home":"001,003,012", "pl_arm_nite":"001,002,013", "retain":"True", "cmd_t":"' + UIC + '/cmnd", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)
        ad_dev = '"avty_t":"' + UIC + '/connect/main", "device":{"identifiers":"' + str(imei) + '"}'
        temp = (cfg.server['AD_PREF'] + "/sensor/" + UIB + "/ip/config", '{"name":"IP", "uniq_id":"' + UIB + '/ip", "stat_t":"' + UIC + '/connect/ip", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)
        temp = (cfg.server['AD_PREF'] + "/sensor/" + UIB + "/port/config", '{"name":"Port", "uniq_id":"' + UIB + '/port", "stat_t":"' + UIC + '/connect/port", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)
        temp = (cfg.server['AD_PREF'] + "/sensor/" + UIB + "/time/config", '{"name":"Connected", "uniq_id":"' + UIB + '/time", "stat_t":"' + UIC + '/connect/time", ' + ad_dev + '}', 1, True)
        msgsAD.append(temp)

def make_msg_status(imei, type, id, ke, value):
    current_device = cfg.search_device(imei)
    url = cfg.server['OKO_PREF'] + '/' + str(current_device['id']) + '/' + str(type)
    if type != 'mode':
         url = url + '/' + str(id+1) + '/' + str(ke)
    temp = (url, value, 1, True)
    msgsST.append(temp)

def make_msg_connect(dev_id, type, value):
    st = {0: 'offline', 1: 'online'}
    state = st.get(value)
    if type[:2] == "ex":
        url = cfg.server['OKO_PREF'] + '/' + dev_id + '/connect/' + str(type[:3])
        temp = (url, state, 1, True)
        for msg in msgsCN:
            if temp == msg:
                break
        else:
            msgsCN.append(temp)

def compare_device_status(oldStatus, newStatus):
    current_device = cfg.search_device(newStatus['imei'])
    ddiff = DeepDiff(oldStatus, newStatus, ignore_order=False, verbose_level=2)
    logging.debug(f"ddiff {ddiff}")
    if ddiff:

        for key, value in ddiff.items():
            if key == 'values_changed':
                for key, value in value.items():
                    work_with_value (newStatus['imei'], "U", key, value['new_value'])
            elif key == 'dictionary_item_added':
                for key, value in value.items():
                    work_with_value (newStatus['imei'], "A", key, value)
                etc.write_JSON_file(cfg.devices, './config/devices.json')
            elif key == 'dictionary_item_removed':
                for key, value in value.items():
                    work_with_value (newStatus['imei'], "D", key, value)
            else:
                logging.info("[" + str(current_device['id']) + "] No ddiff values")

        
        
        if len(msgsAD) > 0:
            logging.debug("[" + str(current_device['id']) + "] " + " try autoDiscovery")
            try:
                publish.multiple(msgsAD, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth={'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']})
                logging.info("[" + str(current_device['id']) + "] Publish " + str(len(msgsAD)) + " autoDiscovery messages")
            except:
                logging.error("Failed to connect to MQTT server")
        else:
            logging.debug("[" + str(current_device['id']) + "] " + "0 autoDiscovery")
        

        #temp = (cfg.server['OKO_PREF'] + '/' + str(current_device['id']) + '/' + "connect/state", 'online', 1, True)
        #msgsST.append(temp)
        if len(msgsST) > 0:
            logging.debug("[" + str(current_device['id']) + "] Try to publish " + str(len(msgsST)) + " status messages")
            try:
                publish.multiple(msgsST, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']})
                logging.info("[" + str(current_device['id']) + "] Published " + str(len(msgsST)) + " status messages")
            except:
                logging.error("Failed to connect to MQTT server")
        else:
            logging.debug("[" + str(current_device['id']) + "] " + "0 status messages")


        if len(msgsCN) > 0:
            logging.debug("[" + str(current_device['id']) + "] Try to publish " + str(len(msgsST)) + " connect messages")
            try:
                publish.multiple(msgsCN, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']})
                logging.info("[" + str(current_device['id']) + "] Published " + str(len(msgsCN)) + " connect messages")
            except:
                logging.error("Failed to connect to MQTT server")
        else:
            logging.debug("[" + str(current_device['id']) + "] " + "0 status messages")

        return True
    else:
        return False

def cmnd(id, pin, conn, address):

    cfg.logs()

    def on_cmnd_receive(client, userdata, message):
        cmd = message.payload.decode()
        msg = "COMMAND:" + pin + cmd + ",70;"
        msg = msg.encode()
        try:
            conn.send(msg)
            logging.info("[" + str(id) + "] Cmnd send")
            logging.debug("[" + str(id) + "] Cmnd " + str(cmd))
            return True
        except:
            logging.info("[" + str(id) + "] Cmnd send ERROR")
            logging.debug("[" + str(id) + "] Cmnd " + str(cmd))
            return False
        

    #logging.info("[" + str(id) + "] Subscribe on cmnd topic")
    msgsST.clear()
    topic = cfg.server['OKO_PREF'] + '/' + str(id) + '/' + "connect/"
    temp = (topic + "main", 'online', 1, True)
    msgsST.append(temp)
    temp = (topic + "ip", str(address[0]), 1, True)
    msgsST.append(temp)
    temp = (topic + "port", str(address[1]), 1, True)
    msgsST.append(temp)
    temp = (topic + "time", str(datetime.today().strftime("%H:%M:%S %d-%m-%Y")), 1, True)
    msgsST.append(temp)
    #topic = topic + "state"
    try:
        logging.debug("[" + str(id) + "] Try to publish connect topic")
        publish.multiple(msgsST, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']}) #keepalive=60, will = {'topic':topic, 'payload':'offline', 'qos':1, 'retain': True}, 
        logging.info("[" + str(id) + "] Published connect topic")
        
        logging.debug("[" + str(id) + "] Try to subscribe on cmnd topic")
        subscribe.callback(on_cmnd_receive, cfg.server['OKO_PREF'] + '/' + str(id) + '/cmnd', hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt', auth = {'username':cfg.server['MQTT_USER'], 'password':cfg.server['MQTT_PASSWORD']}) #will = {'topic':topic, 'payload':'offline', 'qos':1, 'retain': False}, 
        logging.info("[" + str(id) + "] Subscribed on cmnd topic")
    except:
        #("error")
        logging.error("Failed to connect to MQTT server")
      