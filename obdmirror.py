import os
import pygame
import time
import random
import pygame.freetype
import gpsd
import logging
import obd

from gpiozero import LED
from signal import pause

#obd.logger.setLevel(obd.logging.DEBUG)

red = LED(17)
red.blink(on_time=10, off_time=1, background=True)

connection = None

gpsconnected = False

def configobd(port='/dev/pts/3'):
    global connection

    connection = obd.Async('/dev/pts/3')

    for command in [obd.commands.COOLANT_TEMP,
                obd.commands.RPM,
                obd.commands.SPEED,
                obd.commands.INTAKE_TEMP,
                obd.commands.THROTTLE_POS,
                obd.commands.TIMING_ADVANCE,
                obd.commands.SHORT_FUEL_TRIM_1,
                obd.commands.LONG_FUEL_TRIM_1,
                obd.commands.SHORT_FUEL_TRIM_2,
                obd.commands.LONG_FUEL_TRIM_2,
                ]:
        connection.watch(command)

    connection.start()

def configgps():
    global gpsconnected
    while not gpsconnected:
        try:
            gpsd.connect()
            gpsconnected=True
        except:
            logging.critical('No GPS connection present. TIME NOT SET.')
            time.sleep(0.5)

class carmirror(object):
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
        print("Framebuffer size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        self.huge_font = pygame.font.Font("segoeuil.ttf", 240)
        self.ui_font = pygame.font.Font("segoeuil.ttf", 90)
        self.sub_font = pygame.font.Font("segoeuil.ttf", 48)
        self.tiny_font = pygame.font.Font("segoeuil.ttf", 36)
        # Render the screen
        pygame.mouse.set_visible(False)
        pygame.display.update()

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

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def drawtext(self, font, text, position, color=(255,255,255)):
        text = font.render(str(text), True, color)
        self.screen.blit(text, position)

    def clearscreen(self):
        self.screen.fill(self._BLACK)

    def formatresponse(self, r, precision=0):
        try:
            return "{value:.{precision}f}".format(value=r.value.magnitude, precision=precision)
        except:
            return 'N/A'

    def infoscreen(self, title, message, x=100):
        self.clearscreen()
        self.drawfluent(title, message, self._FLUENT_MED, (10,x) )
        pygame.display.update()

    def codes(self):
        self.infoscreen("checking DTCs", "Please wait", x=10)

        connection.stop()
        connection.watch(obd.commands.GET_DTC)
        connection.start()
        time.sleep(2)
        r = connection.query(obd.commands.GET_DTC)

        if r.value:
            msg = "DTC Count {0}".format(len(r.value))

            self.infoscreen(msg, "DTCs", x=10)
            time.sleep(3)

        connection.stop()
        connection.unwatch(obd.commands.GET_DTC)
        connection.start()

    def obd_main(self):
            try:
                self.clearscreen()

                r = self.formatresponse(connection.query(obd.commands.SPEED))
                self.drawfluent(r, "speed", self._FLUENT_LARGE, (260,190) )

                r = self.formatresponse(connection.query(obd.commands.RPM))
                self.drawfluent(r, "rpm", self._FLUENT_SMALL, (10,10) )

                r = self.formatresponse(connection.query(obd.commands.COOLANT_TEMP))
                self.drawfluent(r, "ect", self._FLUENT_MED, (10,90) )

                r = self.formatresponse(connection.query(obd.commands.INTAKE_TEMP))
                self.drawfluent(r, "iat", self._FLUENT_MED, (10,220) )

                r = self.formatresponse(connection.query(obd.commands.THROTTLE_POS))
                self.drawfluent(r, "tps%", self._FLUENT_SMALL, (10,350) )

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

    def gpsscreen(self):
            try:
                self.clearscreen()
                packet = gpsd.get_current()

                if packet.mode >= 2:
                    r = int(packet.hspeed)
                    self.drawfluent(r, "speed", self._FLUENT_LARGE, (260,160) )

                    r = packet.time
                    self.drawfluent(r, "time", self._FLUENT_SMALL, (10,10) )

                    r = int(packet.alt)
                    self.drawfluent(r, "altitude", self._FLUENT_SMALL, (10,90) )

                    r = int(packet.track)
                    self.drawfluent(r, "heading", self._FLUENT_SMALL, (10,170) )

                    r = "{0:.4f}".format(packet.lat)
                    self.drawfluent(r, "latitude", self._FLUENT_SMALL, (10,250) )

                    r = "{0:.4f}".format(packet.lon)
                    self.drawfluent(r, "longitude", self._FLUENT_SMALL, (10,330) )


                else:
                    self.drawtext(self.ui_font, "No GPS", (10,10))

            except KeyboardInterrupt:
                pass

            except:
                self.drawtext(self.ui_font, "GPS Error", (10,10))
                logging.exception('GPS Failure.. ')

            pygame.display.update()


# Create an instance of the PyScope class
if __name__ == '__main__':
    scope = carmirror()
    scope.infoscreen("starting OBD", "Please wait")
    configobd()
    scope.infoscreen("starting GPS", "Please wait")
    configgps()
    scope.codes()
    while True:
        for x in range(300):
            scope.gpsscreen()
        for x in range(300):
            scope.obd_main()




