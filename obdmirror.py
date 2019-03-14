import os
import time
import logging
import obd
from collections import namedtuple
from pathlib import Path
import ast

from gpiozero import LED, Button, Servo

from carmirror import Carmirror

#obd.logger.setLevel(obd.logging.DEBUG)

altunitraw = os.getenv('ALTUNIT', 'False')
altunit = ast.literal_eval(altunitraw)

def setscreen(rev_gpio):
    screen_reverse_pin = LED(rev_gpio)
    screen_reverse_pin.blink(on_time=10, off_time=1, background=True)

if __name__ == '__main__':

    reverse_pin = int(os.getenv('REV_GPIO', 17))
    servo_gpio = int(os.getenv('SERVO_GPIO', 27))
    backup_in = int(os.getenv('BACKUP_GPIO', 22))

    obd_port = os.getenv('OBD_PORT', '/dev/ttyACM0')

    logging.warning('Reverse activate pin {0}'.format(reverse_pin))
    logging.warning('ELM327 OBD Serial port {0}'.format(obd_port))
    logging.warning('Use Alt Units - (Imperial) {0}'.format(altunit))

    #Set screen on pin
    setscreen(reverse_pin)

    #Could not make this work in a function.. Or a thread..
    if servo_gpio and backup_in:
        logging.warning('Setting up 2 way video switch on GPIO {0} triggered by {1}.'.format(servo_gpio, backup_in))
        backup = Button(backup_in)

        init_servo = 1 if backup.value else -1
        servo = Servo(servo_gpio, initial_value=init_servo)

        backup.when_pressed = servo.max
        backup.when_released = servo.min


    mirror = Carmirror(gps=True, obd_port = obd_port, altunit=altunit)
    mirror.infoscreen("starting OBD", "Please wait")
    mirror.configobd()

    mirror.infoscreen("starting GPS", "Please wait")
    mirror.configgps()
    if mirror.connection:
        mirror.codes()

    gauges = [
                {'command': obd.commands.SPEED, 'title': 'speed', 'max': 200, 'warn': 135, 'alt_u': 'mph', 'titleunits': True},
                {'command': obd.commands.RPM, 'title': 'rpm', 'max': 6500, 'warn': 5900, 'alt_u': None, 'titleunits': False},
                {'command': obd.commands.ENGINE_LOAD, 'title': 'load %', 'max': 100, 'warn': 90, 'titleunits': False},
            ]


    while True:
        for x in range(600):
            mirror.accelerometer()
        for x in range(600):
            mirror.gpsscreen()
        if True:
            logging.warning(mirror.connection.status())
            for x in range(600):
                mirror.obd_main()
            for x in range(600):
                mirror.obd_airfuel()
        for gauge in gauges:
            for x in range(600):
                mirror.obd_gauge(**gauge)
