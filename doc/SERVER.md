### Server config params description
#### Socket section  
configuring params for socket server
```
"SOCKET_PORT": 31200,
"SOCKET_TIMEOUT": 90,
"SOCKET_IP": "0.0.0.0",
"SOCKET_LISTEN": 5,
```

**SOCKET_PORT** - TCP port to accept OKO devices connections  
> OKO devices supports different TCP port for the first and second server, but they are the same both for GPRS and Wi-Fi connection.  
>
> While GPRS connection setup your firewall to accept and forward traffic to your server. (meanwhile you can change port at this stage)  
>
>While Wi-Fi connection configure this port to be exactly the same as at device.  

**SOCKET_TIMEOUT** - Timeout in seconds to close OKO devices connections
>If no data is received during this time, the socket connection will be closed.  
>
>This value must be greater than report sending interval configured at device.

**SOCKET_IP** - IP address to accept OKO devices connections
>By setting to 0.0.0.0 accept accept OKO devices connection at any IP address

**SOCKET_LISTEN** - The maximum length of the pending connections queue.
>Change this parameter ONLY if you know what you are doing!

<img src="https://github.com/xyzroe/oko2mqtt/blob/main/doc/img/oko_data_transfer.png?raw=true" width="60%">  

#### MQTT section
configuring params to connect to MQTT server
```
"MQTT_USER": " ",
"MQTT_PASSWORD": " ",
"MQTT_IP": "127.0.0.1",
"MQTT_PORT": 1883,
"OKO_PREF": "oko",
"AD_ENBL": true,
"AD_PREF": "homeassistant",
```
**MQTT_USER** - MQTT server authentication user  
**MQTT_PASSWORD** - MQTT server authentication password   
**MQTT_IP** - MQTT server IP address  
**MQTT_PORT** - MQTT server IP port  
**OKO_PREF**- The prefix for the devices topics  
**AD_ENBL** -  Auto discovery publishing enabled or not  
**AD_PREF** - The prefix for the auto discovery topics  

#### Other section  
configuring other application settings
```
"LOG_LEVEL": 30

```
**LOG_LEVEL** - Logging level  

| Level | Value |
|--- | --- |
| CRITICAL | 50 |
| ERROR | 40 |
| WARNING | 30 |
| INFO | 20 |
| DEBUG | 10 |

### [Begin](https://github.com/xyzroe/oko2mqtt/blob/main/doc/BEGIN.md)
