import picamera, io, threading
import picamera.array
import numpy as np
from time import sleep
from PIL import Image
from Timer import Timer


class BugEye:

    def __init__(self, interval=5000, resolution=(320, 240)):
        self.prev_lum = 0
        self.interval = interval
        self.camera = picamera.PiCamera()
        self.camera.resolution = resolution
        self.stream = picamera.array.PiRGBArray(self.camera)
        self.camera.exposure_mode = 'auto'
        self.camera.awb_mode = 'fluorescent'
        print("Initializing Pi Camera")
        sleep(2)
        self.light_trigger = False
        self.timer = Timer(interval+1)
        self.exposure_thread = threading.Thread(target=self.light_change_detection)
        self.exposure_thread.start()
        sleep(2)

    def light_change_detection(self):
        if self.timer.elapsed_time() > self.interval:
            self.get_exposure()
            if self.cur_lum > self.prev_lum * 1.5 or self.cur_lum < self.prev_lum * .5 and self.prev_lum > 0:
                self.light_trigger = True
                print('Light Change detected!')
            self.timer.start()
            self.prev_lum = self.cur_lum

    def get_exposure(self, channel=0):
        self.camera.exposure_mode = 'off'
        self.ss = self.camera.exposure_speed
        self.gain = float(self.camera.analog_gain) * float(self.camera.digital_gain)
        self.camera.capture(self.stream, format='rgb')
        self.RGB = self.stream.array
        self.cur_lum = self.exp2lum(self.ss, self.gain, np.average(self.RGB[...]))
        print('SS: ', self.ss, ' Gain: ', self.gain, ' Pix value: ', np.average(self.RGB[..., channel]), ' Lum: ', self.cur_lum)
        self.camera.exposure_mode = 'auto'
        self.stream.truncate()
        self.stream.seek(0)

    def estimate_channel_luminance(self):
        RL = self.exp2lum(self.ss, self.gain, np.average(self.RGB[..., 0]))
        GL = self.exp2lum(self.ss, self.gain, np.average(self.RGB[..., 1]))
        BL = self.exp2lum(self.ss, self.gain, np.average(self.RGB[..., 2]))
        return RL, GL, BL

    def snapshot(self):
        img = Image.fromarray(self.RGB.astype('uint8'), 'RGB')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        output = img_byte_arr.getvalue()
        return output

    def light_change_detected(self):
        if self.light_trigger:
            self.light_trigger = False
            return True
        return False

    @staticmethod
    def exp2lum(ss, gain, px):  # convert exposure to lumens
        EV = np.log2(np.power(px / 128, 1.8) * (4000000 / ss) * (1.848 / gain))
        return np.power(2, EV) / 8 if EV >= 0 else 1 / np.power(EV, 2) / 8

