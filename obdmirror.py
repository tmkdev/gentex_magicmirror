import os
import time
import logging
import obd
from collections import namedtuple
from pathlib import Path
import ast
import math

from gpiozero import LED, Button, Servo

from carmirror import Carmirror
from arduino import Arduino

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


    arduino = Arduino('/dev/arduino')
    arduino.start()

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
                {'command': obd.commands.COOLANT_TEMP, 'title': 'coolant temp', 'min': -40, 'max': 215, 'warn': 100, 'alt_u': 'degF', 'titleunits': True},
                {'command': obd.commands.INTAKE_TEMP, 'title': 'intake temp', 'min': -40, 'max': 215, 'warn': 50, 'alt_u': 'degF', 'titleunits': True},
                {'command': obd.commands.TIMING_ADVANCE, 'title': 'timing adv deg', 'min': -64, 'max': 64, 'titleunits': False},
            ]


    currentscreen = 0
    buttonpressed = False

    while True:
        buttons = arduino.get_value('BTNS')

        if buttons and not buttonpressed:
            buttonpressed = True
            if int(buttons) == 1:
                currentscreen += 1
            elif int(buttons) == 2:
                currentscreen -= 1
            elif int(buttons) == 3: # Set fav for now.. 
                currentscreen = 4
        elif not buttons:
            buttonpressed = False

        currentscreen = currentscreen % 10

        if currentscreen == 0:
            ax = (random.gauss(0.6, 0.2) - 0.5) * 2
            ay = (random.gauss(0.6, 0.2) - 0.5) * 2
            mirror.accelerometer(ax, ay, 0, 0)

        if currentscreen == 1:
            mirror.gpsscreen()
        if currentscreen == 2:
            mirror.obd_main()
        if currentscreen == 3:
            mirror.obd_airfuel()
        if currentscreen == 4:
            mirror.obd_gauge(**gauges[0])
        if currentscreen == 5:
            mirror.obd_gauge(**gauges[1])
        if currentscreen == 6:
            mirror.obd_gauge(**gauges[2])
        if currentscreen == 7:
            mirror.obd_gauge(**gauges[3])
        if currentscreen == 8:
            mirror.obd_gauge(**gauges[4])
        if currentscreen == 9:
            mirror.obd_gauge(**gauges[5])
