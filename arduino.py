import serial
import threading
import logging
import re
import time

class Arduino(threading.Thread):
    _keys = ['BTNS', 'AX', 'AY', 'AZ', 'CALX', 'CALY', 'CALZ']

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.data = {'MAX': 0, 'MAY': 0, 'MAZ': 0}

        self.ser = serial.Serial(self.port, 115200, timeout=0)

        self.daemon = True

    def run(self):
        linematch=re.compile('([A-Za-z]+):([0-9.\-]+)')

        linearray = []
        line=None

        with self.ser as s:
            while True:
                line=None
                for c in s.read():
                    linearray.append(c)
                    if c == 13:
                        line = ''.join([chr(x) for x in linearray])
                        linearray=[]
                        break

                if line:
                    parsed  = linematch.search(line)

                    if parsed:
                        entity = parsed.group(1)
                        value = float(parsed.group(2))
                        if entity in self._keys:
                            self.data[entity] = value
                            self.checkmax(entity, value)
                            logging.info(self.data)


    def checkmax(self, key, value):
        if re.match('A[XYZ]', key):
            maxkey = 'M' + key
            if abs(value) > self.data[maxkey]:
                self.data[maxkey] = abs(value)

    def get_value(self, key):
        try:
            return self.data[key]
        except KeyError:
            logging.warning('Arduino data - missing key - {0}'.format(key))
            return 0

if __name__ == '__main__':
    t = Arduino('/dev/arduino')
    t.start()

    try:
        while True:
            print(t.get_value('AZ'))
            print(t.get_value('MAZ'))


    except KeyboardInterrupt:
        logging.warning('Done..')

    t.join()

