## HUMIDITY TEMPERATURE
import time
import board
import adafruit_dht


class THSensor:
    def __init__(self):
        # Initial the dht device, with data pin connected to:
        self.dhtDevice = adafruit_dht.DHT22(board.D4)

    def get_humidity(self):
        h = False
        while not h:
            try:
                h = self.dhtDevice.humidity
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                time.sleep(1.0)
                continue
            except Exception as error:
                self.dhtDevice.exit()
                raise error
        return h

    def get_temperature(self):
        t = False
        while not t:
            try:
                t = self.dhtDevice.temperature
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                time.sleep(1.0)
                continue
            except Exception as error:
                self.dhtDevice.exit()
                raise error
        return t

    def exit(self):
        self.dhtDevice.exit()