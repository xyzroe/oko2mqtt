### Device config params description  
The program fills the file with all the necessary attributes when connecting a new device or adding a new sensor according to the template and the received information.  

If you need, you can enable or disable the processing of any of the elements, as you can change the names, icons, classes.

Device send almost all sensors data every package, don't take care if sensor exists or not.  

However some sensors data arrives only if sensor exists and configured.  
*(DS18B20 sensors, radio sensors, counters, extension boards, radio sockets)*

#### Main section  
**You must set unique `id` attribute.**  
You can change `name` attribute.  

You can change `pin` attribute if you what control device.  
You can set `code` attribute to be asked code while control device state from HA.  

Attributes `imei`, `hw`, `sw` are system, please don't edit them unless you know what you do.   
```
    "imei": "861230040XXXXXX",
    "name": "Unknown",
    "id": "unk",
    "pin": "1234",
    "hw": "OKO-EX",
    "sw": "E.4.2",
    "code": "7777",
```

#### General section  
Total `8` items.   
To process item, the attribute `name` must be set.
First 5 items use `class` attribute.  
Last 5 items use `icon` attribute.
```
    "general": [
        {
            "name": "Tamper",
            "class": "safety"
        },
        {
            "name": "Режим охраны",
            "icon": "mdi:security"
        }
    ],
```

#### Groups section  
Total `8` items.   
To process item, the attributes `name` and `icon` must be set.  
```
    "groups": [
        {
            "name": "Group X",
            "icon": "mdi:group"
        },
    ],
```

#### Outputs section  
Total `8` items.   
To process item, the attributes `name` and `icon` must be set.
```
    "outputs": [
        {
            "name": "Output X",
            "icon": "mdi:flash"
        },
    ],  
```

#### Inputs section  
Total `8` items.
To process item, the attributes `name` and `class` must be set.  
Also to process short and cut states, the attributes `short` and `cut` must be set `true`.
```
    "inputs": [
        {
            "name": "Input X",
            "class": "window",
            "short": true,
            "cut": false
        },
    ],
```

#### ADCs section  
Total `5` items.   
To process item, the attributes `name` and `icon` must be set.
```
    "adcs": [
        {
            "name": "ADC X",
            "icon": "mdi:speedometer"
        },
    ],
```

#### DS18B20 sensors section  
Total `8` items.   
To process item, the attributes `name` must be set and `class` must be set `temperature`.
```
    "dallas": [
        {
            "name": "DS18B20 X",
            "class": "temperature"
        },
    ],
```

#### Radio sensors section  
Total `16` items.   
To process item, the attributes `name` and `class` must be set.

Attribute `sensor_type` is system, please don't edit it unless you know what you do.   
Possible values: `magnet, event, fire, remote_simple, remote, temp_extender, temp`

```
    "radios": [
        {
            "name": "Radio X",
            "class": "window",
            "sensor_type": "magnet"
        },
    ],
```

#### Counters section  
Total `8` items.   
To process item, the attributes `name` and `icon` must be set.
```
    "counters": [
        {
            "name": "Counter X",
            "icon": "mdi:numeric"
        },
    ],
```

#### Others section  
Total `8` items.   
To process item, the attributes `name` and `icon` must be set.  
First 5 items are extension boards 0, 1, 2, 3, 4 states.  
Sixth item is radio sockets states.  
Last 2 items are OKO service data type and value.
```
    "others": [
        {
            "name": "EX X",
            "icon": "mdi:file-question"
        },
    ],
```

### Auto Discovery config params description  
Attribute `icon` set icon.  
MDI icons. Prefix name with `mdi:`, ie `mdi:home`.    

Attribute `class` set device class.  
Most sensors use [binary sensor device class](https://www.home-assistant.io/integrations/binary_sensor/#device-class) .    
 GSM Level, DS18B20s, ADCs, Counters, Others use [sensor device class](https://www.home-assistant.io/integrations/sensor/#device-class).  

You can set `code` attribute to be asked code while control device state from HA.  

*The attributes `icon`, `class`, `code` are only used when `AD_ENBL` set to `true` in `server.json`, but you should not remove them either `AD_ENBL` set to `false`*

### [Begin](./BEGIN.md)
