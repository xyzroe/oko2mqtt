# -*- coding: utf-8 -*-
import logging, json

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

msg_codes = read_JSON_file('./dev/msg_codes.json')


