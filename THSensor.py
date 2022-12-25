## HUMIDITY TEMPERATURE
import time
import board
import adafruit_dht


class THSensor:
    def __init__(self):
        # Initial the dht device, with data pin connected to:
        self.dhtDevice = adafruit_dht.DHT22(board.D4)

    def get_humidity(self):
        return self.dhtDevice.humidity

    def get_temperature(self):
        return self.dhtDevice.temperature

    def exit(self):
        self.dhtDevice.exit()