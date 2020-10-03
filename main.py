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


class Callback:
    """Callback for the measure loop of the DHT sensor."""

    def __init__(
            self,
            client,
            temperature_state_topic,
            humidity_state_topic,
            logger=None,
            homeassistant_config_fn=None,
            repeat_config_every=15
    ):
        """Create the callback function that sends sensor data over MQTT.

        Parameters
        ----------
        client : mqtt.Client
            A MQTT client which will send the data.
        temperature_state_topic : float
            A topic to post temperature data to.
        humidity_state_topic : float
            A topic to post humidity data to.
        logger: logging.Logger or None
            The logger instance.
        homeassistant_config_fn: Callable
            Function which will configure the sensor for Home Assistant.
            By including it here, it will be called periodically, defined by
            repeat_config_every. Doing this will ensure the sensor will be
            recognized by Home Assistant, even after outages and restarts.
        repeat_config_every: int
            Call the homeassistant_config_fn every repeat_config_every times
            this callback is called.


        Returns
        -------
        Function
            The callback function which process data to send over MQTT.

        """
        self.counter = 0
        self.client = client
        self.temperature_state_topic = temperature_state_topic
        self.humidity_state_topic = humidity_state_topic
        self.logger = logger
        self.config_fn = homeassistant_config_fn
        self.repeat_config_every = repeat_config_every

    def __call__(self, temperature, humidity):
        """Send temperature/humidity over MQTT.

        Parameters
        ----------
        temperature : float
            Temperature readout from the DHT sensor.
        humidity : float
            Humidity readout from the DHT sensor
        """
        if self.config_fn is not None \
                and self.counter % self.repeat_config_every == 0:
            self.config_fn()

        if self.logger is not None:
            logger.info(
                "New measurement: Temperature=%s, Humidity=%s",
                temperature,
                humidity
            )
        if self.temperature_state_topic == self.humidity_state_topic:
            client.publish(
                self.temperature_state_topic,
                json.dumps({"temperature": temperature, "humidity": humidity})
            )
        else:
            client.publish(
                self.temperature_state_topic,
                json.dumps({"temperature": temperature})
            )
            client.publish(
                self.humidity_state_topic,
                json.dumps({"humidity": humidity})
            )
        self.counter += 1


class HomeAssistantConfigFn:
    """Publish the sensor configuration to Home Assistant."""

    def __init__(
            self,
            client,
            config,
            mqtt_config,
            logger=None,
            topics=("temperature", "humidity")
    ):
        """Initialize the config function.

        Parameters
        ----------
        client : mqtt.Client
            The client which will publish the config data to the MQTT broker.
        config : dict
            The config dictionary
        mqtt_config : dict
            The MQTT config dictionary
        logger : logging.Logger or None
            The Logger instance
        topics : tuple(str, ...)
            All the topics to configure
        """
        self.client = client
        self.config = config
        self.mqtt_config = mqtt_config
        self.logger = logger
        self.topics = topics

    def __call__(self):
        """Publish the sensor configuration to Home Assistant."""
        for topic_name in self.topics:
            base_topic = self.mqtt_config[topic_name + "_base_topic"]

            if base_topic[-1] != "/":
                base_topic += "/"

            # Publish the configuration values to the broker.
            self.client.publish(
                base_topic + "config",
                json.dumps(dict(self.config["MQTT_%s" % topic_name]))
            )

            if self.logger is not None:
                logger.info(
                    "Published topic %s for %s",
                    base_topic,
                    topic_name
                )


def init_logging(log_config):
    """Initialize the logging.

    Parameters
    ----------
    log_config : dict or None
        Configuration for the loggin.

    Returns
    -------
    logging.Logger or None
        Logger instance.

    """
    if log_config is None:
        return None

    level_string = log_config["level_stream"]

    # Add stdoutput
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(log_config["format_stream"])
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(getattr(logging, level_string.upper()))
    logger.addHandler(stream_handler)

    # Add log file if defined in the config
    if "file" in log_config and len(log_config["file"]):
        level_string = log_config["level_file"]
        file_handler = logging.FileHandler(log_config["file"])
        formatter = logging.Formatter(log_config["format_file"])
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level_string.upper()))
        logger.addHandler(file_handler)

    return logger


def init_mqtt(mqtt_config, logger=None):
    """Initialize the MQTT client.

    Parameters
    ----------
    mqtt_config : dict
        MQTT configuration.
    logger : logging.Logger or None
        Logger instance.

    Returns
    -------
    mqtt.Client
        Logged in MQTT client.
    """
    if logger is not None:
        logger.info("Initializing MQTT client...")

    # Define basic client information
    client = mqtt.Client()
    host = mqtt_config["host"]
    port = int(mqtt_config["port"])

    # Add credentials
    if "username" in mqtt_config and "password" in mqtt_config:
        client.username_pw_set(
            mqtt_config["username"],
            mqtt_config["password"]
        )

    # Add TLS/SSL options
    if MQTT_TLS_KEY in config and len(config[MQTT_TLS_KEY]):
        client.tls_set(**config[MQTT_TLS_KEY])

    # Connect to the MQTT broker
    client.connect(host, port)

    if logger is not None:
        logger.info("MQTT client connected to broker %s:%s", host, port)

    # Start the MQTT loop. This is necessary to keep the connection alive.
    client.loop_start()

    return client


def init_sensor(sensor_config, logger=None):
    """Intialize sensor.

    Parameters
    ----------
    sensor_config : dict
        Sensor configuration values.
    logger : logging.Logger or None
        Logger instance

    Returns
    -------
    DHTSensor
        DHT Sensor to read.
    """
    if logger is not None:
        logger.info("Initializing The DHT Sensor...")

    # General sensor setup
    sensor_type = sensor_config["sensor_type"]
    pin = sensor_config["pin"]
    temperature_unit = sensor_config["temperature_unit"]
    sensor = DHTSensor(
        sensor_type,
        pin,
        temperature_unit
    )

    if logger is not None:
        logger.info(
            "%s Sensor initialized on pin %s (unit = %s)",
            sensor_type,
            pin,
            temperature_unit
        )

    return sensor


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

    # Parse arguments
    args = parser.parse_args()

    # Parse the config
    config = configparser.RawConfigParser()
    config.read(args.config)
    config = config_as_dict(config)

    # Define specific config sections
    if LOG_KEY in config:
        log_config = config[LOG_KEY]
    else:
        logger = None
    mqtt_config = config[MQTT_KEY]
    sensor_config = config[DHT_KEY]

    # Initialize everything
    logger = init_logging(log_config)
    client = init_mqtt(mqtt_config, logger)
    sensor = init_sensor(sensor_config, logger)

    # Check if config should be repeated
    if "repeat_config_every" in mqtt_config:
        repeat_every = int(mqtt_config["repeat_config_every"])
    else:
        repeat_every = None

    # Go into daemon mode
    logger.info("Starting measurement loop...")
    sensor.measure_loop(
        Callback(
            client,
            config["MQTT_temperature"]["state_topic"],
            config["MQTT_humidity"]["state_topic"],
            logger,
            HomeAssistantConfigFn(client, config, mqtt_config, logger),
            repeat_every
        ),
        int(sensor_config["time_between_measurements"])
    )
