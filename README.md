DHT - MQTT Sensor
=================
The code in this repository allows you to measure a DHT sensor with your
Raspberry Pi or BeagleBone device.

Installation
============
Clone the repository and install the required dependencies.
```
git clone https://www.github.com/berndie/dht-mqtt
cd dht_mqtt
(sudo) pip(3) install -r requirements.txt
```

Copy `config.ini.dist` to `config.ini` and edit this file to suit your specific
needs. You need to at least set the `pin` and `host` in the configuration file.

```
cp config.ini.dist config.ini
nano config.ini
```

Running the script
==================
Run the main script

```
(sudo) python(3) main.py
```

Installing the script as a daemon
=================================
To install this script as a service, run:
```
sudo python(3) install_service.py
```
This will install a `dht_mqtt.service` in `/lib/systemd/system/`.

You can start the service by running:
```
sudo systemctl start dht_mqtt.service
```

You can enable the service to run on boot by running:
```
sudo systemctl enable dht_mqtt.service
```

TODO
====
* Unittesting
* Enable CI on this repository
* Checking compatibility for different python versions


License
=======
MIT License

Copyright (c) 2020 Bernd Accou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
