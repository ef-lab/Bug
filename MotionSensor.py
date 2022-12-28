## MOTION
import RPi.GPIO as GPIO  # Import GPIO library
from Timer import Timer


class MotionSensor:
    def __init__(self):
        self.motion_trigger = False
        self.GPIO = GPIO
        self.timer = Timer()
        self.GPIO.setmode(self.GPIO.BCM)  # Set GPIO pin numbering
        pir = 26  # Associate pin 26 to pir
        self.GPIO.setup(pir, self.GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.GPIO.add_event_detect(pir, self.GPIO.RISING,
                                   callback=self._motion_detection, bouncetime=200)

    def motion_detected(self):
        if self.motion_trigger:
            self.motion_trigger = False
            return True
        return False

    def _motion_detection(self, channel):
        print('Motion Detected!')
        self.motion_trigger = True

    def exit(self):
        self.GPIO.cleanup()

