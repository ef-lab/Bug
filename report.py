from Logger import *
from Camera import *
from THSensor import *
from MotionSensor import *

log_interval = 10  # interval in seconds
room = "A000"

logger = Logger()
cam = BugEye()
ths = THSensor()
mot = MotionSensor()
log_timer = Timer()
time.sleep(2)

while True:
    if log_timer.elapsed_time() > log_interval*1000:
        # log temp, hum, luminance
        tmst = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        key = dict(room_id=room, tmst=tmst, celcius=ths.get_temperature())
        logger.log('Temperature', key, schema='monitoring', priority=10)

        key = dict(room_id=room, tmst=tmst, relative_humidity=ths.get_humidity())
        logger.log('Humidity', key, schema='monitoring', priority=10)

        RL, GL, BL = cam.estimate_channel_luminance()
        key = dict(room_id=room, tmst=tmst, r_channel=RL, g_channel=GL, b_channel=BL, trigger='time')
        logger.log('Luminance', key, schema='monitoring', priority=10)

        # restart timer
        log_timer.start()

    if mot.motion_detected():
        tmst = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # capture image
        im = cam.snapshot()

        # log image
        key = dict(room_id=room, tmst=tmst, image=im, trigger='motion')
        logger.log('Camera', key, schema='monitoring', priority=10)

        # log motion
        key = dict(room_id=room, tmst=tmst)
        logger.log('Motion', key, schema='monitoring', priority=10)

    cam.light_change_detection()
    if cam.light_change_detected():
        RL, GL, BL = cam.estimate_channel_luminance()
        key = dict(room_id=room, tmst=tmst, r_channel=RL, g_channel=GL, b_channel=BL, trigger='light')
        logger.log('Luminance', key, schema='monitoring', priority=10)

    time.sleep(.1)

