import numpy, socket, json, os, pathlib, threading, subprocess, time
from queue import PriorityQueue
from datetime import datetime
from dataclasses import dataclass
from dataclasses import field as datafield
from typing import Any
import datajoint as dj

dj.config["enable_python_native_blobs"] = True

schemata = {'common': 'lab_common',
            'monitoring': 'lab_monitoring'}

for schema, value in schemata.items():  # separate connection for internal comminication
    globals()[schema] = dj.create_virtual_module(schema, value, create_tables=True, create_schema=True)


class Timer:
    """ This is a timer that is used for the state system
    time is in milliseconds
    """
    def __init__(self):
        self.start_time = 0
        self.time = time.time
        self.start()

    def start(self):
        self.start_time = self.time()

    def elapsed_time(self):
        return int((self.time() - self.start_time) * 1000)

    def add_delay(self, sec):
        self.start_time += sec

class Logger:
    trial_key, setup_info, _schemata, datasets = dict(animal_id=0, session=1, trial_idx=0), dict(), dict(), dict()
    lock, queue, ping_timer, logger_timer, total_reward, curr_state = False, PriorityQueue(), Timer(), Timer(), 0, ''

    def __init__(self):
        self.setup = socket.gethostname()
        self.is_pi = os.uname()[4][:3] == 'arm' if os.name == 'posix' else False
        fileobject = open(os.path.dirname(os.path.abspath(__file__)) + '/dj_local_conf.json')
        con_info = json.loads(fileobject.read())
        self.private_conn = dj.Connection(con_info['database.host'], con_info['database.user'],
                                          con_info['database.password'])
        for schema, value in schemata.items():  # separate connection for internal comminication
            self._schemata.update({schema: dj.create_virtual_module(schema, value, connection=self.private_conn)})
        self.thread_end, self.thread_lock = threading.Event(), threading.Lock()
        self.inserter_thread = threading.Thread(target=self.inserter)
        self.getter_thread = threading.Thread(target=self.getter)
        self.inserter_thread.start()
        self.getter_thread.start()
        self.logger_timer.start()
        self.Writer = Writer

    def setup_schema(self, extra_schema):
        for schema, value in extra_schema.items():
            globals()[schema] = dj.create_virtual_module(schema, value, create_tables=True, create_schema=True)
            self._schemata.update({schema: dj.create_virtual_module(schema, value, connection=self.private_conn)})

    def put(self, **kwargs):
        item = PrioritizedItem(**kwargs)
        self.queue.put(item)
        if not item.block:
            self.queue.task_done()
        else:
            self.queue.join()

    def inserter(self):
        while not self.thread_end.is_set():
            if self.queue.empty():  time.sleep(.5); continue
            item = self.queue.get()
            skip = False if item.replace else True
            table = rgetattr(self._schemata[item.schema], item.table)
            self.thread_lock.acquire()
            try:
                table.insert1(item.tuple, ignore_extra_fields=item.ignore_extra_fields,
                              skip_duplicates=skip, replace=item.replace)
                if item.validate:  # validate tuple exists in database
                    key = {k: v for (k, v) in item.tuple.items() if k in table.primary_key}
                    if 'status' in item.tuple.keys(): key['status'] = item.tuple['status']
                    while not len(table & key) > 0: time.sleep(.5)
            except Exception as e:
                if item.error: self.thread_end.set(); raise
                print('Failed to insert:\n', item.tuple, '\n in ', table, '\n With error:\n', e, '\nWill retry later')
                item.error = True
                item.priority = item.priority + 2
                self.queue.put(item)
            self.thread_lock.release()
            if item.block: self.queue.task_done()

    def getter(self):
        while not self.thread_end.is_set():
            self.thread_lock.acquire()
            self.setup_info = (self._schemata['experiment'].Control() & dict(setup=self.setup)).fetch1()
            self.thread_lock.release()
            self.setup_status = self.setup_info['status']
            time.sleep(1)  # update once a second

    def log(self, table, data=dict(), **kwargs):
        tmst = self.logger_timer.elapsed_time()
        self.put(table=table, tuple={**self.trial_key, 'time': tmst, **data}, **kwargs)
        if self.manual_run and table == 'Trial.StateOnset': print('State: ', data['state'])
        return tmst

    def update_setup_info(self, info, key=dict()):
        self.setup_info = {**(experiment.Control() & {**{'setup': self.setup}, **key}).fetch1(), **info}
        block = True if 'status' in info else False
        self.put(table='Control', tuple=self.setup_info, replace=True, priority=1, block=block, validate=block)
        self.setup_status = self.setup_info['status']

    def get(self, schema='experiment', table='Control', fields='', key=dict(), **kwargs):
        table = rgetattr(eval(schema), table)
        return (table() & key).fetch(*fields, **kwargs)

    def ping(self, period=5000):
        if self.ping_timer.elapsed_time() >= period:  # occasionally update control table
            self.ping_timer.start()
            self.update_setup_info({'last_ping': str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                    'queue_size': self.queue.qsize(), 'trials': self.trial_key['trial_idx'],
                                    'total_liquid': self.total_reward, 'state': self.curr_state})

    def cleanup(self):
        while not self.queue.empty(): print('Waiting for empty queue... qsize: %d' % self.queue.qsize()); time.sleep(1)
        self.thread_end.set()

    @staticmethod
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80)); IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    @staticmethod
    def rgetattr(obj, attr, *args):
        def _getattr(obj, attr): return getattr(obj, attr, *args)

        return functools.reduce(_getattr, [obj] + attr.split('.'))


@dataclass(order=True)
class PrioritizedItem:
    table: str = datafield(compare=False)
    tuple: Any = datafield(compare=False)
    field: str = datafield(compare=False, default='')
    value: Any = datafield(compare=False, default='')
    schema: str = datafield(compare=False, default='experiment')
    replace: bool = datafield(compare=False, default=False)
    block: bool = datafield(compare=False, default=False)
    validate: bool = datafield(compare=False, default=False)
    priority: int = datafield(default=50)
    error: bool = datafield(compare=False, default=False)
    ignore_extra_fields: bool = datafield(compare=False, default=True)


@monitoring.schema
class Temperature(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    celcius                  : float                        # in celcius
    """


@monitoring.schema
class Humidity(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    relative_humidity             : float            # in percent
    """


@monitoring.schema
class Motion(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    """


@monitoring.schema
class Light(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    ---
    r_lumens             : float            # in cd per sqm
    g_lumens             : float            # in cd per sqm
    b_lumens             : float            # in cd per sqm
    trigger="time"           : enum('time', 'light')    # Trigger 
    """


@monitoring.schema
class Camera(dj.Manual):
    definition = """
    # room temperature
    -> common.Room
    tmst                     : timestamp                    # measurement timestamp
    --- 
    image             : mediumblob            # in Image  uint8 format
    trigger="time"           : enum('time', 'motion', 'light', 'sound')    # Trigger 
    """