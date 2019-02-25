import os
import pygame
import time
import random
import pygame.freetype
import gpsd
import logging
import obd
from collections import namedtuple
from pathlib import Path

from gpiozero import LED

#obd.logger.setLevel(obd.logging.DEBUG)

TextDef = namedtuple('TextDef', ['value_expression', 'displayname', 'size', 'position', 'unit_alt'])

connection = None
gpsconnected = False
altunit = True

commandlist = {
    'dtc': ['GET_DTC'],
    'obdmain': [
        'ENGINE_LOAD',
        'COOLANT_TEMP',
        'SHORT_FUEL_TRIM_1',
        'LONG_FUEL_TRIM_1',
        'SHORT_FUEL_TRIM_2',
        'LONG_FUEL_TRIM_2',
        'RPM',
        'SPEED',
        'TIMING_ADVANCE',
        'INTAKE_TEMP',
        'THROTTLE_POS'
    ],
    'airfuel': [
        'SHORT_FUEL_TRIM_1',
        'LONG_FUEL_TRIM_1',
        'SHORT_FUEL_TRIM_2',
        'LONG_FUEL_TRIM_2',
        'O2_B1S1',
        'O2_B1S2',
        'O2_B2S1',
        'O2_B2S2',
        'COMMANDED_EGR',
        'EGR_ERROR',
        'MAF',
        'INTAKE_PRESSURE',
        'RPM',
        'SPEED',
    ]
}

currentcommandlist = None

def setscreen(rev_gpio):
    screen_reverse_pin = LED(rev_gpio)
    screen_reverse_pin.blink(on_time=10, off_time=1, background=True)

def setcommandlist(listname):
    global connection, currentcommandlist
    if currentcommandlist != listname:
        connection.stop()
        connection.unwatch_all()

        for command in commandlist[listname]:
            connection.watch(obd.commands[command])

        currentcommandlist = listname

        connection.start()


def configobd(port='/dev/pts/3'):
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

class Carmirror(object):
    screen = None
    _WHITE = (255,255,255)
    _GREY = (128,128,128)
    _BLACK = (0,0,0)

    _FLUENT_SMALL = 0
    _FLUENT_MED = 1
    _FLUENT_LARGE = 2

    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print("I'm running under X display = {0}".format(disp_no))

        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print('Driver: {0} failed.'.format(driver))
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        logging.warning("Framebuffer size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        self.huge_font = pygame.font.Font("assets/selawkl.ttf", 240)
        self.ui_font = pygame.font.Font("assets/selawkl.ttf", 90)
        self.sub_font = pygame.font.Font("assets/selawkl.ttf", 48)
        self.tiny_font = pygame.font.Font("assets/selawkl.ttf", 36)
        # Render the screen
        pygame.mouse.set_visible(False)
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def drawfluent(self, pritext, titletext, size=_FLUENT_MED, position=(0,0)):
        if size == self._FLUENT_SMALL:
            self.drawtext(self.tiny_font, titletext, position, self._GREY)
            self.drawtext(self.sub_font, pritext, (position[0], position[1]+30), self._WHITE)
        if size == self._FLUENT_MED:
            self.drawtext(self.sub_font, titletext, position, self._GREY)
            self.drawtext(self.ui_font, pritext, (position[0], position[1]+30), self._WHITE)
        if size == self._FLUENT_LARGE:
            self.drawtext(self.sub_font, titletext, position, self._GREY)
            self.drawtext(self.huge_font, pritext, position, self._WHITE)

    def drawtext(self, font, text, position, color=(255,255,255)):
        text = font.render(str(text), True, color)
        self.screen.blit(text, position)

    def clearscreen(self):
        self.screen.fill(self._BLACK)

    def formatresponse(self, r, precision=0, alt_u= None):
        try:
            if altunit and alt_u:
                r = r.value.to(alt_u)
                value = r.magnitude
            else:
                value = r.value.magnitude
            return "{value:.{precision}f}".format(value=value, precision=precision)

        except AttributeError:
            return 'N/A'
        except:
            logging.exception('formatresponse failed')
            return 'N/A'

    def map_heading(self, heading):
        if heading >  337.5 or heading < 22.5:
            return 'N'
        if heading >=22.5 and heading < 67.5:
            return 'NE'
        if heading >= 67.5 and heading < 112.5:
            return 'E'
        if heading >= 112.5 and heading < 157.5:
            return 'SE'
        if heading >= 157.5 and heading < 202.5:
            return 'S'
        if heading >= 205.5 and heading < 247.5:
            return 'SW'
        if heading >= 247.5 and heading < 292.5:
            return 'W'
        if heading >= 292.5 and heading < 337.5:
            return 'NW'

    def infoscreen(self, title, message, x=100):
        self.clearscreen()
        self.drawfluent(title, message, self._FLUENT_MED, (10,x) )
        pygame.display.update()

    def codes(self):
        self.infoscreen("checking DTCs", "please wait")

        setcommandlist('dtc')
        time.sleep(2)
        r = connection.query(obd.commands.GET_DTC)

        if r.value:
            msg = "DTC Count {0}".format(len(r.value))
            self.infoscreen(msg, "DTCs")
            time.sleep(3)

    def obd_main(self):
            setcommandlist('obdmain')

            try:
                self.clearscreen()

                r = self.formatresponse(connection.query(obd.commands.SPEED), alt_u='mph')
                self.drawfluent(r, "speed", self._FLUENT_LARGE, (260,190) )

                r = self.formatresponse(connection.query(obd.commands.RPM))
                self.drawfluent(r, "rpm", self._FLUENT_SMALL, (10,10) )

                r = self.formatresponse(connection.query(obd.commands.COOLANT_TEMP), alt_u='degF')
                self.drawfluent(r, "ect", self._FLUENT_MED, (10,90) )

                r = self.formatresponse(connection.query(obd.commands.INTAKE_TEMP), alt_u='degF')
                self.drawfluent(r, "iat", self._FLUENT_MED, (10,220) )

                r = self.formatresponse(connection.query(obd.commands.THROTTLE_POS))
                self.drawfluent(r, "tps%", self._FLUENT_SMALL, (10,350) )

                r = self.formatresponse(connection.query(obd.commands.ENGINE_LOAD))
                self.drawfluent(r, "load", self._FLUENT_SMALL, (120,350) )

                r = self.formatresponse(connection.query(obd.commands.TIMING_ADVANCE))
                self.drawfluent(r, "advance", self._FLUENT_SMALL, (140,10) )

                r = self.formatresponse(connection.query(obd.commands.SHORT_FUEL_TRIM_1))
                self.drawfluent(r, "stft1", self._FLUENT_SMALL, (300,10) )

                r = self.formatresponse(connection.query(obd.commands.LONG_FUEL_TRIM_1))
                self.drawfluent(r, "ltft1", self._FLUENT_SMALL, (420,10) )

                r = self.formatresponse(connection.query(obd.commands.SHORT_FUEL_TRIM_2))
                self.drawfluent(r, "stft2", self._FLUENT_SMALL, (300,90) )

                r = self.formatresponse(connection.query(obd.commands.LONG_FUEL_TRIM_2))
                self.drawfluent(r, "ltft2", self._FLUENT_SMALL, (420,90) )

            except KeyboardInterrupt:
                pass

            except:
                self.drawtext(self.ui_font, "OBD Error", (10,10))
                logging.exception('OBD Failure.. ')

            pygame.display.update()

            #pygame.image.save(self.screen, "obd_screen.jpg")


    def obd_airfuel(self):
            setcommandlist('airfuel')

            try:
                self.clearscreen()

                raw = connection.query(obd.commands.MAF)
                r = self.formatresponse(raw, precision=0)
                self.drawfluent(r, "maf {:~}".format(raw.value.units), self._FLUENT_SMALL, (10,10) )

                raw = connection.query(obd.commands.COMMANDED_EGR)
                r = self.formatresponse(raw)
                self.drawfluent(r, "cmd egr%", self._FLUENT_SMALL, (10,90) )

                raw = connection.query(obd.commands.EGR_ERROR)
                r = self.formatresponse(raw)
                self.drawfluent(r, "egr error%", self._FLUENT_SMALL, (10,170) )

                raw = connection.query(obd.commands.INTAKE_PRESSURE)
                r = self.formatresponse(raw,  precision=1)
                self.drawfluent(r, "map kpa", self._FLUENT_SMALL, (10,250) )

                raw = connection.query(obd.commands.SPEED)
                r = self.formatresponse(raw, alt_u='mph')
                self.drawfluent(r, "speed {:~}".format(raw.value.units), self._FLUENT_SMALL, (10,330) )

                r = self.formatresponse(connection.query(obd.commands.RPM))
                self.drawfluent(r, "RPM", self._FLUENT_SMALL, (290,330) )

                raw = connection.query(obd.commands.SHORT_FUEL_TRIM_1)
                r = self.formatresponse(raw, precision=2)
                self.drawfluent(r, "stft1", self._FLUENT_SMALL, (290,10) )

                raw = connection.query(obd.commands.LONG_FUEL_TRIM_1)
                r = self.formatresponse(raw, precision=2)
                self.drawfluent(r, "ltft1", self._FLUENT_SMALL, (430,10) )

                raw = connection.query(obd.commands.SHORT_FUEL_TRIM_2)
                r = self.formatresponse(raw, precision=2)
                self.drawfluent(r, "stft2", self._FLUENT_SMALL, (290,90) )

                raw = connection.query(obd.commands.LONG_FUEL_TRIM_2)
                r = self.formatresponse(raw, precision=2)
                self.drawfluent(r, "ltft2", self._FLUENT_SMALL, (430,90) )

                r = self.formatresponse(connection.query(obd.commands.O2_B1S1), precision=2)
                self.drawfluent(r, "o2 b1 s1", self._FLUENT_SMALL, (290,170) )

                r = self.formatresponse(connection.query(obd.commands.O2_B1S2), precision=2)
                self.drawfluent(r, "o2 b1 s2", self._FLUENT_SMALL, (430,170) )

                r = self.formatresponse(connection.query(obd.commands.O2_B2S1), precision=2)
                self.drawfluent(r, "o2 b2 s1", self._FLUENT_SMALL, (290,250) )

                r = self.formatresponse(connection.query(obd.commands.O2_B2S1), precision=2)
                self.drawfluent(r, "o2 b2 s2", self._FLUENT_SMALL, (430,250) )


            except KeyboardInterrupt:
                pass

            except:
                self.drawtext(self.ui_font, "OBD Error", (10,10))
                logging.exception('OBD Failure.. ')

            pygame.display.update()

            #pygame.image.save(self.screen, "airfuel_screen.jpg")


    def gpsscreen(self):
            try:
                self.clearscreen()
                packet = gpsd.get_current()

                if packet.mode >= 2:
                    r = (packet.hspeed * obd.Unit['meter/second']).to(obd.Unit.kph)
                    if altunit:
                        r=r.to('mph')
                    self.drawfluent(int(r.magnitude), "speed {:~}".format(r.units), self._FLUENT_LARGE, (260,160) )

                    r = packet.get_time(local_time=True)
                    self.drawfluent(r.strftime('%a, %b %d %Y %-H:%M:%S'), "time", self._FLUENT_SMALL, (10,10) )

                    r = packet.alt * obd.Unit.meter
                    if altunit:
                        r=r.to('ft')
                    self.drawfluent(int(r.magnitude), "altitude {:~}".format(r.units), self._FLUENT_SMALL, (10,90) )

                    r = packet.track
                    h = self.map_heading(r)
                    rtext = '{0:.0f} {1}'.format(r, h)
                    self.drawfluent(rtext, "heading", self._FLUENT_SMALL, (10,170) )

                    r = "{0:.4f}".format(packet.lat)
                    self.drawfluent(r, "latitude", self._FLUENT_SMALL, (10,250) )

                    r = "{0:.4f}".format(packet.lon)
                    self.drawfluent(r, "longitude", self._FLUENT_SMALL, (10,330) )

                else:
                    self.drawtext(self.ui_font, "No GPS", (10,100))

            except KeyboardInterrupt:
                pass

            except:
                self.drawtext(self.ui_font, "GPS Error", (10,10))
                logging.exception('GPS Failure.. ')

            pygame.display.update()

            #pygame.image.save(self.screen, "gps_screen.jpg")

# Create an instance of the PyScope class
if __name__ == '__main__':
    reverse_pin = int(os.getenv('REV_GPIO', 17))
    obd_port = os.getenv('OBD_PORT', '/dev/ttyACM0')

    logging.warning('Reverse activate pin {0}'.format(reverse_pin))
    logging.warning('ELM327 OBD Serial port {0}'.format(obd_port))
    logging.warning('Use Alt Units - (Imperial) {0}'.format(altunit))

    setscreen(reverse_pin)

    mirror = Carmirror()
    mirror.infoscreen("starting OBD", "Please wait")
    configobd(obd_port)

    mirror.infoscreen("starting GPS", "Please wait")
    configgps()
    if connection:
        mirror.codes()

    while True:
        for x in range(300):
            mirror.gpsscreen()
        if connection:
            logging.warning(connection.status())
            for x in range(300):
                mirror.obd_main()
            for x in range(300):
                mirror.obd_airfuel()




