import picamera, io, threading
import picamera.array
import numpy as np
from time import sleep
from PIL import Image
from Timer import Timer


class BugEye:
    def __init__(self):
        self.capture_thread = threading.Thread(target=self.light_change_detection)
        self.prev_lum = 0
        self.camera = picamera.PiCamera()
        self.stream = picamera.array.PiRGBArray(self.camera)
        self.camera.exposure_mode = 'auto'
        self.camera.awb_mode = 'auto'
        self.light_trigger = False
        self.timer = Timer()
        print("Initializing Pi Camera")
        sleep(2)
        self.capture_thread.start()

    def light_change_detection(self):
        if self.timer.elapsed_time() > 1000:
            self.get_exposure()
            if self.cur_lum > self.prev_lum * 1.5 or self.cur_lum < self.prev_lum * .5 and self.prev_lum > 0:
                self.light_trigger = True

    def get_exposure(self, channel=0):
        self.camera.exposure_mode = 'off'
        self.camera.capture(self.stream, format='rgb')

        ss = self.camera.exposure_speed
        gain = float(self.camera.analog_gain) * float(self.camera.digital_gain)
        RGB = self.stream.array
        self.cur_lum = self.exp2lum(ss, gain, np.average(RGB[..., channel]))

        self.camera.exposure_mode = 'auto'
        self.prev_lum = self.cur_lum
        self.stream.truncate()
        self.stream.seek(0)

        return ss, gain, RGB

    def estimate_channel_luminance(self):
        sleep(1)
        ss, gain, RGB = self.get_exposure()
        RL = self.exp2lum(ss, gain, np.average(RGB[..., 0]))
        GL = self.exp2lum(ss, gain, np.average(RGB[..., 1]))
        BL = self.exp2lum(ss, gain, np.average(RGB[..., 2]))
        return RL, GL, BL

    def snapshot(self):
        ss, gain, array = self.get_exposure()
        img = Image.fromarray(array.astype('uint8'), 'RGB')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        output = img_byte_arr.getvalue()
        return output

    def save_jpeg(self, file='image', array=False):
        if not array:
            stream = io.BytesIO(array)
            img = Image.open(stream)
        image = Image.fromarray(array.astype('uint8'), 'RGB')
        image.save(file + ".jpg")

    def light_change_detected(self):
        if self.light_trigger:
            self.light_trigger = False
            return True
        return False

    @staticmethod
    def exp2lum(ss, gain, px):  # convert exposure to lumens
        EV = np.power(px / 128, 2.2) * np.log2((4000000 / ss) * (1.848 / gain))
        return np.power(2, EV) / 8 if EV >= 0 else 1 / np.power(2, EV) / 8

