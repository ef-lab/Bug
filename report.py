from Logger import *
from Camera import *
from THSensor import *
from MotionSensor import *

log_interval = 3600  # interval in seconds
room = "A000"

logger = Logger()
cam = BugEye()
ths = THSensor()
mot = MotionSensor()
log_timer = Timer()

while True:
    if log_timer.elapsed_time() > log_interval*1000:
        # log temp, hum, luminance
        tmst = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        key = dict(room=room, tmst=tmst, celcius=ths.get_temperature())
        logger.log('Temperature', key, schema='monitoring', priority=10)

        key = dict(room=room, tmst=tmst, relative_humidity=ths.get_humidity())
        logger.log('Humidity', key, schema='monitoring', priority=10)

        RL, GL, BL = cam.estimate_channel_luminance()
        key = dict(room=room, tmst=tmst, R_luminance=RL, G_luminance=GL, B_luminance=BL, trigger='time')
        logger.log('Light', key, schema='monitoring', priority=10)

        # restart timer
        log_timer.start()

    if mot.motion_detected():
        tmst = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # capture image
        im = cam.snapshot()

        # log image
        key = dict(room=room, tmst=tmst, image=im, trigger='motion')
        logger.log('Camera', key, schema='monitoring', priority=10)

        # log motion
        key = dict(room=room, tmst=tmst)
        logger.log('Motion', key, schema='monitoring', priority=10)

    if cam.light_change_detected():
        RL, GL, BL = cam.estimate_channel_luminance()
        key = dict(room=room, tmst=tmst, R_luminance=RL, G_luminance=GL, B_luminance=BL, trigger='light')
        logger.log('Light', key, schema='monitoring', priority=10)

    time.sleep(.1)
