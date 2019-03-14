import serial
import threading
import logging
import re
import time

class Arduino(threading.Thread):
    _keys = ['BTNS', 'AX', 'AY', 'AZ']

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.data = {}

        self.ser = serial.Serial(self.port, 115200, timeout=0.5)

        self.daemon = True

    def run(self):
        linematch=re.compile('([A-Za-z]+):([0-9.])+')

        lock = threading.Lock()

        while True:
            with self.ser as s:
                try:
                    line=self.ser.readline()
                    if line:
                        linestring = line.decode('ascii')

                        parsed  = linematch.match(linestring)

                        if parsed:
                            entity = parsed.group(1)
                            value = float(parsed.group(2))
                            if entity in self._keys:
                                lock.acquire()
                                self.data[entity] = value
                                lock.release()
                                logging.info(self.data)

                except:
                    logging.exception('Something wrong in arduino serial data class')

    def get_value(self, key):
        try:
            return self.data[key]
        except KeyError:
            logging.warning('Arduino data - missing key - {0}'.format(key))
            return None

if __name__ == '__main__':
    t = Arduino('/dev/arduino')
    t.start()

    t.get_value('test')

    t.join()

