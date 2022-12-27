import numpy, socket, json, os, pathlib, threading, subprocess, time, functools
from queue import PriorityQueue
from datetime import datetime
from dataclasses import dataclass
from dataclasses import field as datafield
from typing import Any
import datajoint as dj
from Timer import Timer

dj.config["enable_python_native_blobs"] = True

schemata = {'common': 'lab_common',
            'monitoring': 'lab_monitoring'}

for schema, value in schemata.items():  # separate connection for internal comminication
    globals()[schema] = dj.create_virtual_module(schema, value, create_tables=True, create_schema=True)

from Tables import *


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
        self.inserter_thread.start()
        self.logger_timer.start()

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
            table = self.rgetattr(self._schemata[item.schema], item.table)
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

    def log(self, table, data=dict(), **kwargs):
        self.put(table=table, tuple=data, **kwargs)

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