# 👁 oko2mqtt

## Description
Allows you to use your OKO security alarm devices without the manufacture server.

It bridges states and allows you to control your OKO devices via MQTT using your own server.

This way, you can integrate your OKO devices into whatever smart home infrastructure you use.  

[MQTT Auto Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) supports, so it does all the work for you if using Home Assistant.


## Getting started
[Documentation](https://github.com/xyzroe/oko2mqtt/blob/main/doc/BEGIN.md) provides you all the information you need to get started!

## Supported devices
All [ОКО](https://око.укр/) security alarms that use [OKO TCP socket](https://github.com/xyzroe/oko2mqtt/blob/main/doc/etc/OKO_socket.pdf) protocol.    
They are models with [GSM-controllers](https://око.укр/ohrannaya-signalizaciya/gsm-dozvonshchiki/) (ОКО-PRO/U2/7S/PRO-X/OKO-EX).

## Home Assistant Lovelace UI
![](https://github.com/xyzroe/oko2mqtt/blob/master/doc/img/ha_lovelace_oko.png?raw=true)
