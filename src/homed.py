# -*- coding: utf-8 -*-
import logging, json

import paho.mqtt.publish as publish

from src import cfg

# fd (from device) messages queued for the current compare_device_status() run
msgsHomed = []

# per device_id: {expose_name: {"on": "<oko cmnd payload>", "off": "<oko cmnd payload>"}}
write_map = {}


def _topic(sub):
    return cfg.server['AD_PREF_HOMED'] + '/' + sub


# HOMEd expose names must be camelCase; underscore is only allowed right before a numeric index
_BASE_NAMES = {
    'inputs': 'input', 'outputs': 'output', 'groups': 'group',
    'ex1_in': 'ex1In', 'ex2_in': 'ex2In', 'ex3_in': 'ex3In', 'ex4_in': 'ex4In',
    'ex1_out': 'ex1Out', 'ex2_out': 'ex2Out', 'ex3_out': 'ex3Out', 'ex4_out': 'ex4Out',
    'sockets_bkl1': 'socketsBkl1', 'sockets_bkl2': 'socketsBkl2',
    'sockets_bkl3': 'socketsBkl3', 'sockets_bkl4': 'socketsBkl4',
    'adcs': 'adc', 'dallas': 'dallas', 'counters': 'counter', 'others': 'other',
    'address-sensors': 'addressSensor', 'radios': 'radio',
}


def _cap(word):
    return word[0].upper() + word[1:] if word else word


def _indexed_name(type, id, ke=None):
    name = _BASE_NAMES[type] + '_' + str(id + 1)
    if ke:
        name += _cap(ke)
    return name


def _binary(class_=None):
    opt = {"type": "binary"}
    if class_:
        opt["class"] = class_
    return opt


def _sensor(unit=None, class_=None):
    opt = {"type": "sensor"}
    if class_:
        opt["class"] = class_
    if unit:
        opt["unit"] = unit
    return opt


def _toggle(title=None):
    opt = {"type": "toggle"}
    if title:
        opt["title"] = title
    return opt


def _general_exposes(device):
    # slot: (ke, kind, class/unit, title, on/off oko payloads for writable slots)
    slots = {
        0: ('tamper', 'binary', 'safety', 'Tamper', None),
        1: ('power', 'binary', 'plug', 'Power supply', None),
        2: ('bat12v', 'binary', 'battery', '12V battery', None),
        3: ('bat5v', 'binary', 'battery', '5V battery', None),
        4: ('gsm', 'sensor', 'dBm', 'GSM level', None),
        5: ('code', 'sensor', None, 'Status code', None),
        6: ('txt', 'sensor', None, 'Status', None),
        7: ('balance', 'sensor', None, 'Balance', None),
        8: ('siren', 'toggle', None, 'Siren', ('4', '3')),
        9: ('armed', 'toggle', None, 'Security mode', ('01', '00')),
    }
    result = []
    for id, item in enumerate(device['general']):
        if not item:
            continue
        ke, kind, extra, title, onoff = slots[id]
        name = ke
        if kind == 'binary':
            result.append((name, _binary(extra), ke, None))
        elif kind == 'sensor':
            result.append((name, _sensor(extra), ke, None))
        else:
            result.append((name, _toggle(title), ke, onoff))
    return result


def _in_group_exposes(device, type):
    result = []
    for id, item in enumerate(device[type]):
        if not item:
            continue
        if item.get('class'):
            result.append((_indexed_name(type, id, 'alarm'), _binary(item['class']), 'alarm', None))
        if item.get('cut'):
            result.append((_indexed_name(type, id, 'cut'), _binary('problem'), 'cut', None))
        if item.get('short'):
            result.append((_indexed_name(type, id, 'short'), _binary('problem'), 'short', None))
    return result


def _out_group_exposes(device, type, pl_prefix=''):
    result = []
    for id, item in enumerate(device[type]):
        if not item:
            continue
        name = _indexed_name(type, id)
        if type == 'outputs':
            onoff = ('*#' + str(id + 1) + '9', '*#' + str(id + 1) + '0')
        elif type == 'groups':
            onoff = ('01' + str(id + 1), '00' + str(id + 1))
        else:
            ex = type[2:3]
            onoff = ('*' + ex + '#' + str(id + 1) + '9', '*' + ex + '#' + str(id + 1) + '0')
        result.append((name, _toggle(item.get('name')), 'state', onoff))
    return result


def _value_group_exposes(device, type, ke, unit=None, class_=None):
    result = []
    for id, item in enumerate(device[type]):
        if not item:
            continue
        name = _indexed_name(type, id)
        result.append((name, _sensor(unit, item.get('class', class_)), ke, None))
    return result


def _radios_exposes(device):
    result = []
    keys = {
        'low_battery': ('battery', 'binary'),
        'tamper': ('safety', 'binary'),
        'alarm': (None, 'binary'),
        'test': ('moving', 'binary'),
        'sos': (None, 'binary'),
        'home': (None, 'binary'),
        'open': (None, 'binary'),
        'close': (None, 'binary'),
        'temp': ('°C', 'sensor'),
    }
    for id, item in enumerate(device['radios']):
        if not item:
            continue
        for ke, (extra, kind) in keys.items():
            name = _indexed_name('radios', id, ke)
            if kind == 'binary':
                result.append((name, _binary(extra), ke, None))
            else:
                result.append((name, _sensor(extra), ke, None))
    return result


def build_device_data(device):
    exposes = []
    options = {}
    payloads = {}

    for name, opt, ke, onoff in _general_exposes(device):
        exposes.append(name)
        options[name] = opt
        if onoff:
            payloads[name] = {'on': onoff[0], 'off': onoff[1]}

    for type in ['inputs', 'ex1_in', 'ex2_in', 'ex3_in', 'ex4_in']:
        for name, opt, ke, onoff in _in_group_exposes(device, type):
            exposes.append(name)
            options[name] = opt

    for type in ['outputs', 'groups', 'ex1_out', 'ex2_out', 'ex3_out', 'ex4_out',
                 'sockets_bkl1', 'sockets_bkl2', 'sockets_bkl3', 'sockets_bkl4']:
        for name, opt, ke, onoff in _out_group_exposes(device, type):
            exposes.append(name)
            options[name] = opt
            payloads[name] = {'on': onoff[0], 'off': onoff[1]}

    for name, opt, ke, onoff in _value_group_exposes(device, 'adcs', 'value', 'V'):
        exposes.append(name)
        options[name] = opt
    for name, opt, ke, onoff in _value_group_exposes(device, 'dallas', 'value', '°C', 'temperature'):
        exposes.append(name)
        options[name] = opt
    for name, opt, ke, onoff in _value_group_exposes(device, 'counters', 'count'):
        exposes.append(name)
        options[name] = opt
    for name, opt, ke, onoff in _value_group_exposes(device, 'others', 'value'):
        exposes.append(name)
        options[name] = opt
    for name, opt, ke, onoff in _value_group_exposes(device, 'address-sensors', 'value'):
        exposes.append(name)
        options[name] = opt

    for name, opt, ke, onoff in _radios_exposes(device):
        exposes.append(name)
        options[name] = opt

    if device.get('mode'):
        exposes.append('mode')
        options['mode'] = _sensor()

    data = {
        'active': True,
        'id': device['id'],
        'name': device['name'],
        'real': True,
        'discovery': True,
        'exposes': exposes,
        'options': options,
    }
    return data, payloads


def sync_device(device):
    if not cfg.server.get('AD_ENBL_HOMED'):
        return
    if not device or str(device['imei']) == '0':
        return
    try:
        data, payloads = build_device_data(device)
        write_map[device['id']] = payloads
        msg = {'action': 'updateDevice', 'device': device['id'], 'data': data}
        publish.single(_topic('command/custom'), payload=json.dumps(msg), qos=1, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt-homed', auth={'username': cfg.server['MQTT_USER'], 'password': cfg.server['MQTT_PASSWORD']})
        logging.info(f"[{device['id']}] HOMEd device definition published")
    except Exception as err:
        logging.error(f"Failed to connect to MQTT server\n{err}")


def queue_value(device, type, id, ke, value):
    if not cfg.server.get('AD_ENBL_HOMED'):
        return
    if type == 'mode':
        name = 'mode'
    elif type == 'general':
        name = ke
    elif type == 'radios':
        name = _indexed_name(type, id, ke)
    elif type in ('outputs', 'groups') or type[-3:] == 'out' or type[:-1] == 'sockets_bkl':
        name = _indexed_name(type, id)
    elif type in ('inputs',) or type[-2:] == 'in':
        name = _indexed_name(type, id, ke)
    else:
        name = _indexed_name(type, id)

    binary_keys = ('tamper', 'power', 'bat12v', 'bat5v', 'alarm', 'cut', 'short')
    toggle_keys = ('siren', 'armed', 'state')
    if ke in binary_keys or (type in ('inputs',) or type[-2:] == 'in'):
        payload_value = bool(str(value) not in ('0', 'False', 'false'))
    elif ke in toggle_keys:
        payload_value = bool(str(value) not in ('0', 'False', 'false'))
    else:
        payload_value = value

    topic = _topic('fd/custom/' + str(device['id']))
    for existing in msgsHomed:
        if existing[0] == topic:
            existing[1][name] = payload_value
            return
    msgsHomed.append([topic, {name: payload_value}])


def flush(current_device):
    if not cfg.server.get('AD_ENBL_HOMED') or not msgsHomed:
        return
    msgs = [(topic, json.dumps(payload), 0, False) for topic, payload in msgsHomed]
    try:
        publish.multiple(msgs, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt-homed', auth={'username': cfg.server['MQTT_USER'], 'password': cfg.server['MQTT_PASSWORD']})
        logging.info(f"[{current_device['id']}] Published {len(msgs)} HOMEd fd messages")
    except Exception as err:
        logging.error(f"Failed to connect to MQTT server\n{err}")
    finally:
        msgsHomed.clear()


def td_subscription(device_id, cmnd_topic):
    """Returns (topic, callback) for the HOMEd td (to device) topic, or None if HOMEd is disabled."""
    if not cfg.server.get('AD_ENBL_HOMED'):
        return None

    def on_td_receive(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
        except ValueError:
            return
        payloads = write_map.get(device_id, {})
        for name, value in payload.items():
            onoff = payloads.get(name)
            if not onoff:
                continue
            is_on = str(value).lower() in ('true', 'on', '1')
            cmd = onoff['on'] if is_on else onoff['off']
            publish.single(cmnd_topic, payload=cmd, qos=1, hostname=cfg.server['MQTT_IP'], port=cfg.server['MQTT_PORT'], client_id='oko2mqtt-homed-td', auth={'username': cfg.server['MQTT_USER'], 'password': cfg.server['MQTT_PASSWORD']})

    return _topic('td/custom/' + str(device_id)), on_td_receive

