## Principle of work
While first run app will generate two files in `config` folder: `server.json` and `devices.json`  
Each of them contains the corresponding config params. You can edit them at any time to adjust what you need and restart app.  
>`server.json` won't update it self.  
`devices.json` will update when new OKO device connected or data new sensor received.  

At the beginning app start a socket server and wait for connections.  
When new connection starts checks if device already exist at DB, if not adds.   
Messages from known devices parses, looks for difference from last message and send them to MQTT server.  
If there is command from MQTT server and open socket for this device it sends command to device until new status message received.  

<div align="center">
<img src="https://github.com/xyzroe/oko2mqtt/blob/master/doc/img/mqtt_oko.png?raw=true" width="60%">  
</div>

## First run
### Install
#### Docker
```
docker run -d \
  --name oko2mqtt \
  -p 31200:31200 \
  --mount type=bind,source=[HOST]/config,target=/usr/src/app/config \
  xyzroe/oko2mqtt
```
or
#### Local
```
git clone git@github.com:xyzroe/oko2mqtt.git
cd oko2mqtt
pip3 install --no-cache-dir -r requirements.txt
python3 main.py
```
After first start modify params in `server.json` that you need and restart app.

##### [Server config params description](https://github.com/xyzroe/oko2mqtt/blob/master/doc/SERVER.md)  

### Add device
  * Configure data transfer settings in OKO device.
  * Wait device to connect to server and send all data.
  * After first connect modify params in `devices.json` section corresponding to your device IMEI.

##### [Device config params description](https://github.com/xyzroe/oko2mqtt/blob/master/doc/DEVICES.md)

### Using Home Assistant help
You can use Portainer.io to make all setup from GUI in a few steps:

    Create container →   
    Name: `oko2mqtt` →  
    Image: `xyzroe/oko2mqtt:latest` →   
    Manual network port publishing →  
    host: `31200` →  
    container: `31200` →  
    Volumes →   
    container: `/usr/src/app/config` →   
    Bind →   
    host: `/mnt/data/supervisor/share/oko2mqtt` →    
    Restart policy →
    Always →
    Deploy container

Congratulations 🎉

Config dir will be available at `/share/oko2mqtt` from HA file editor.

Auto Discovery allows you to configure all sensors automatically.
You don't need to do this.
You can change the attributes you need according to the [description](https://github.com/xyzroe/oko2mqtt/blob/master/doc/DEVICES.md#auto-discovery-config-params-description)
