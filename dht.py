"""Code to read DHT sensor values.

This code uses and is largely based on the example of the adafruit_dht
library.
"""
import logging
import time
import board
import adafruit_dht

logger = logging.getLogger('DHT-MQTT')


class DHTSensor(adafruit_dht.DHTBase):
    """DHT Sensor class.

    This class allows you to make continous measurements of temperature and
    humidity. It supports both the DHT22 and DHT11 module, as it is a subclass
    of the adafruit-circuitpython-dht DHTBase class.
    """

    def __init__(self, sensor_type, pin, temp_unit="C"):
        """Initialize the DHT sensor.

        Parameters
        ----------
        sensor_type : str
            Sensor type. Must be "DHT11" or "DHT22".
        pin : str
            Pin number, in the format defined by the
            adafruit-circuitpython-dht and board module.
        temp_unit : str
            Temperature unit, must be "C" or "F".
        """
        pin = getattr(board, pin)
        sensor_type = sensor_type.upper()
        self.temp_unit = temp_unit.upper()

        if self.temp_unit not in ("C", "F"):
            raise ValueError("Unsupported temperature unit \"%s\"" % temp_unit)

        if sensor_type in ("DHT11", "DHT22"):
            is_dht11 = sensor_type == "DHT11"
            timeout = 18000 if is_dht11 else 1000
            super(DHTSensor, self).__init__(is_dht11, pin, timeout)
        else:
            raise ValueError("The supported sensors are DHT11 and DHT22")

    @property
    def temperature(self):
        """Get a temperature measurement.

        Returns
        -------
        float
            The temperature measured by the DHT sensor in self.temp_unit.
        """
        temp = super(DHTSensor, self).temperature
        if self.temp_unit == "C":
            return temp
        else:
            return temp * (9 / 5) + 32

    def measure_loop(self, callback, time_between_iterations=2):
        """Start a continous loop which measures the sensor over time.

        Parameters
        ----------
        callback : Function
            A function that processes the measured data. The function will
            receive 2 parameters: temperature and humidity respectively.
        time_between_iterations : int
            The time between measurements cycles in seconds.
        """
        while True:
            try:
                callback(self.temperature, self.humidity)
            except RuntimeError as error:
                logging.warning("DHT measurement failed: %s", str(error))

            time.sleep(time_between_iterations)
