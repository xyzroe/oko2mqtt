<div align="center">
<h1>👁 oko2mqtt</h1>
</div>

## Description
Allows you to use your OKO security alarm devices without the manufacture server

It bridges states and allows you to control your OKO devices via MQTT using your own sever.

This way, you can integrate your OKO devices into whatever smart home infrastructure you use.  

[MQTT Auto Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) supports, so it does all the work for you if using Home Assistant.


## Getting started
The [documentation](./doc/BEGIN.md) provides you all the information needed to get up and running!


## Supported devices
All [ОКО](https://око.укр/) security alarms that use [OKO TCP socket](./doc/etc/OKO_socket.pdf) protocol.    
They are models with [GSM-controllers](https://око.укр/ohrannaya-signalizaciya/gsm-dozvonshchiki/) (ОКО-PRO/U2/7S/PRO-X/OKO-EX).

## HA Lovelace UI
<div align="center">
<img src="./doc/img/ha_lovelace_oko.png" width="95%">  
</div>
