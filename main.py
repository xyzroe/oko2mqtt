#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, time, socket

from threading import Thread
from multiprocessing import Process



import schedule




from src import oko, etc, cfg
  
def client(conn, address):
    logging.warning("New connection from " + str(address))
    newConn = True

    while True:
        time.sleep(0.1) #to avoid 100% CPU usage
        try:
            msg = conn.recv(1024)
        except:
            logging.debug("[" + str(devId) + "] Cannot recieve data")
            break
        if not msg:
            logging.debug("[" + str(devId) + "] No data")
            break
        oko.msgsAD.clear()
        oko.msgsST.clear()
        oko.msgsCN.clear()
        #print(scan_msg(msg.decode()))
        #if msg:
        devId, devPin = oko.scan_msg(msg.decode())
        if newConn and devId and devPin :
            newConn = False
            logging.warning("Start process to handle MQTT cmnds")
            proc = Process(target=oko.cmnd, args=(devId,devPin,conn,address))
            #proc = Thread(target=oko.cmnd, args=(devId,devPin,conn,address), daemon = True)
            proc.start()

    #logging.warning("!!! terminate")
    try: proc.terminate()
    except Exception as err:
        logging.error(f"{err}")

    try: conn.shutdown(socket.SHUT_RDWR)
    except Exception as err:
        logging.error(f"{err}")

    try: conn.close()
    except Exception as err:
        logging.error(f"{err}")

    logging.warning("[" + str(devId) + "] Socket closed")


def check():
    logging.info("Starting schedule thread and tasks")
    schedule.every(30).seconds.do(oko.check_devices_msg)
    while True:
        schedule.run_pending()
        time.sleep(0.1) #to avoid 100% CPU usage

def server():
    logging.warning("Starting server at " + str(cfg.server['SOCKET_IP']) + " on " + str(cfg.server['SOCKET_PORT']))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((cfg.server['SOCKET_IP'], cfg.server['SOCKET_PORT']))
    s.listen(cfg.server['SOCKET_LISTEN'])

    t = Thread(target=check, args=(), daemon = True)
    t.start()

    while True:

        (conn, address) = s.accept()
        conn.settimeout(cfg.server['SOCKET_TIMEOUT'])
        t = Thread(target=client, args=(conn, address), daemon = True)
        t.start()
        time.sleep(0.1) #to avoid 100% CPU usage

def main():
    cfg.logs()
    try: server()
    except KeyboardInterrupt: logging.critical("Keyboard interrupt")


if __name__ == '__main__':
    main()
