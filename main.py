"""Script that continously measures the DHT sensor and publishes it on MQTT."""
import argparse
import configparser
import json
import logging
import os
import sys

import paho.mqtt.client as mqtt

from dht import DHTSensor

logger = logging.getLogger('DHT-MQTT')
logger.setLevel(logging.INFO)

LOG_KEY = "Logging"
DHT_KEY = "DHT"
MQTT_KEY = "MQTT"
MQTT_TLS_KEY = "MQTT_TLS"


def config_as_dict(config):
    """Convert a ConfigParser object into a dictionary.

    The resulting dictionary has sections as keys which point to a dict of the
    sections options as key => value pairs.

    Borrowed from https://stackoverflow.com/a/23944270

    Parameters
    ----------
    config : configparser.BaseConfigParser
        ConfigParser with loaded config files.

    Returns
    -------
    dict:
        A dictionary contain all the config options of config.
    """
    the_dict = {}
    for section in config.sections():
        the_dict[section] = {}
        for key, val in config.items(section):
            the_dict[section][key] = val
    return the_dict


def callback_wrapper(client, temperature_state_topic, humidity_state_topic):
    """Create the callback function that sends sensor data over MQTT.

    Parameters
    ----------
    client : mqtt.Client
        A MQTT client which will send the data.
    temperature_state_topic : float
        A topic to post temperature data to.
    humidity_state_topic : float
        A topic to post humidity data to.

    Returns
    -------
    Function
        The callback function which process data to send over MQTT.

    """

    def callback(temperature, humidity):
        """Send temperature/humidity over MQTT.

        Parameters
        ----------
        temperature : float
            Temperature readout from the DHT sensor.
        humidity : float
            Humidity readout from the DHT sensor
        """
        logger.info(
            "New measurement: Temperature=%s, Humidity=%s",
            temperature,
            humidity
        )
        if temperature_state_topic == humidity_state_topic:
            client.publish(
                temperature_state_topic,
                json.dumps({"temperature": temperature, "humidity": humidity})
            )
        else:
            client.publish(
                temperature_state_topic,
                json.dumps({"temperature": temperature})
            )
            client.publish(
                humidity_state_topic,
                json.dumps({"humidity": humidity})
            )
        client.loop()

    return callback


if __name__ == "__main__":
    folder = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description="Measure temperature/humidity from a "
                    "DHT sensor and publish it to MQTT"
    )
    parser.add_argument(
        "--config",
        default=os.path.join(folder, "config.ini"),
        help="Config file with options for the DHT sensor and MQTT connection"
    )

    args = parser.parse_args()
    config = configparser.RawConfigParser()
    config.read(args.config)
    config = config_as_dict(config)

    # Configure the logging
    log_config = config[LOG_KEY]
    level_string = log_config["level_stream"]
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(log_config["format_stream"])
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(getattr(logging, level_string.upper()))
    logger.addHandler(stream_handler)
    if "file" in log_config and len(log_config["file"]):
        level_string = log_config["level_file"]
        file_handler = logging.FileHandler(log_config["file"])
        formatter = logging.Formatter(log_config["format_file"])
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level_string.upper()))

        logger.addHandler(file_handler)

    # Initialize MQTT client
    mqtt_config = config[MQTT_KEY]
    logger.info("Initializing MQTT client...")
    client = mqtt.Client()
    host = mqtt_config["host"]
    port = int(mqtt_config["port"])

    if "username" in mqtt_config and "password" in mqtt_config:
        client.username_pw_set(
            mqtt_config["username"],
            mqtt_config["password"]
        )

    if MQTT_TLS_KEY in config and len(config[MQTT_TLS_KEY]):
        client.tls_set(**config[MQTT_TLS_KEY])
    client.connect(host, port)
    logger.info("MQTT client connected to broker %s:%s", host, port)

    # Initialize the sensor
    logger.info("Initializing The DHT Sensor...")
    sensor_type = config[DHT_KEY]["sensor_type"]
    pin = config[DHT_KEY]["pin"]
    temperature_unit = config[DHT_KEY]["temperature_unit"]
    sensor = DHTSensor(
        sensor_type,
        pin,
        temperature_unit
    )
    logger.info(
        "%s Sensor initialized on pin %s (unit = %s)",
        sensor_type,
        pin,
        temperature_unit
    )

    # Publish the new sensor on MQTT, so your home assistant/other software can
    # find it
    for topic_name in ("temperature", "humidity"):
        base_topic = mqtt_config[topic_name + "_base_topic"]
        if base_topic[-1] != "/":
            base_topic += "/"
        client.publish(
            base_topic + "config",
            json.dumps(dict(config["MQTT_%s" % topic_name]))
        )
        logger.info("Published topic %s for %s", base_topic, topic_name)

    # Go into daemon mode
    logger.info("Starting measurement loop...")
    sensor.measure_loop(
        callback_wrapper(
            client,
            config["MQTT_temperature"]["state_topic"],
            config["MQTT_humidity"]["state_topic"]
        ),
        int(config[DHT_KEY]["time_between_measurements"])
    )
