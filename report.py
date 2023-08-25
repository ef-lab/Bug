from Logger import *
from Camera import *
from THSensor import *
from MotionSensor import *
import socket

log_interval = 3600  # interval in seconds
motion_interval = 60  # motion detection interval in seconds
camera_interval = 5  # luminance change detection interval in seconds
camera_resolution = (480, 320)  # camera resolution

logger = Logger()
cam = BugEye(interval=camera_interval*1000, resolution=camera_resolution)
ths = THSensor()
mot = MotionSensor()
log_timer = Timer(offset=log_interval*1000+1)
motion_timer = Timer(offset=motion_interval*1000+1)
time.sleep(2)

room = (common.Computer & {'hostname': socket.gethostname()}).fetch1('room_id')
common.Computer().update1({'hostname': socket.gethostname(), 'ping': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))})

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

        # ping
        common.Computer().update1({'hostname': socket.gethostname(), 'ping': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))})

        # restart timer
        log_timer.start()

    if mot.motion_detected() and motion_timer.elapsed_time() > motion_interval*1000:
        tmst = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # capture image
        im = cam.snapshot()

        # log image
        key = dict(room_id=room, tmst=tmst, image=im, trigger='motion')
        logger.log('Camera', key, schema='monitoring', priority=10)

        # log motion
        key = dict(room_id=room, tmst=tmst)
        logger.log('Motion', key, schema='monitoring', priority=10)
        motion_timer.start()

    cam.light_change_detection()
    if cam.light_change_detected():
        tmst = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        RL, GL, BL = cam.estimate_channel_luminance()
        key = dict(room_id=room, tmst=tmst, r_channel=RL, g_channel=GL, b_channel=BL, trigger='light')
        logger.log('Luminance', key, schema='monitoring', priority=10)

    time.sleep(.5)

