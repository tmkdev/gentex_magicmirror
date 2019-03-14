import os
import time
import gpsd
import logging
import obd
from collections import namedtuple
from pathlib import Path
import ast

from carmirror import Carmirror
from gpiozero import LED, Button, Servo
import pint

#obd.logger.setLevel(obd.logging.DEBUG)

ureg = pint.UnitRegistry()

altunitraw = os.getenv('ALTUNIT', 'False')
altunit = ast.literal_eval(altunitraw)

connection = None
gpsconnected = False
currentcommandlist = None


def setscreen(rev_gpio):
    screen_reverse_pin = LED(rev_gpio)
    screen_reverse_pin.blink(on_time=10, off_time=1, background=True)

def setobdcommands(obdcommandlist, listname):
    global connection, currentcommandlist
    if currentcommandlist != listname:
        connection.stop()
        connection.unwatch_all()

        for command in obdcommandlist:
            connection.watch(command)

        currentcommandlist = listname

        connection.start()

def configobd(port='/dev/pts/2'):
    try:
        global connection
        connection = obd.Async(port)
    except:
        logging.critical('No OBD found on {0}'.format(port))


def configgps():
    global gpsconnected
    while not gpsconnected:
        try:
            gpsd.connect()
            gpsconnected=True
        except:
            logging.critical('No GPS connection present. TIME NOT SET.')
            time.sleep(0.5)


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

    mirror = Carmirror()
    mirror.infoscreen("starting OBD", "Please wait")
    configobd(obd_port)

    mirror.infoscreen("starting GPS", "Please wait")
    configgps()
    if connection:
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
        if connection:
            logging.warning(connection.status())
            for x in range(600):
                mirror.obd_main()
            for x in range(600):
                mirror.obd_airfuel()
        for gauge in gauges:
            for x in range(600):
                mirror.obd_gauge(**gauge)
