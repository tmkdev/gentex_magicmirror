import logging
import random
import os
import gpsd
import obd
import time
from math import pi, hypot

import pygame
import pygame.freetype

import pint

ureg = pint.UnitRegistry()

class Carmirror(object):
    screen = None
    _WHITE = (255,255,255)
    _GREY = (128,128,128)
    _DARKGREY = (32,32,32)
    _BLACK = (0,0,0)
    _WARNING = (255,35,0)

    _FLUENT_SMALL = 0
    _FLUENT_MED = 1
    _FLUENT_LARGE = 2

    def __init__(self, gps=None, obd_port=None, altunit=False ):
        self.gps = gps
        self.obd_port = obd_port
        self.altunit = altunit

        self.connection = None
        self.gpsconnected = False
        self.currentcommandlist = None

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
        self.screen.fill(self._BLACK)
        # Initialise font support
        pygame.font.init()
        self.huge_font = pygame.font.Font("assets/selawkl.ttf", 240)
        self.ui_font = pygame.font.Font("assets/selawkl.ttf", 84)
        self.sub_font = pygame.font.Font("assets/selawkl.ttf", 44)
        self.tiny_font = pygame.font.Font("assets/selawkl.ttf", 36)
        # Render the screen
        pygame.mouse.set_visible(False)
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def setobdcommands(self, obdcommandlist, listname):
        if self.currentcommandlist != listname:
            self.connection.stop()
            self.connection.unwatch_all()

            for command in obdcommandlist:
                self.connection.watch(command)

        self.currentcommandlist = listname

        self.connection.start()

    def configobd(self):
        try:
            self.connection = obd.Async(self.obd_port)
        except:
            logging.critical('No OBD found on {0}'.format(self.obd_port))

    def configgps(self):
        while not self.gpsconnected:
            try:
                gpsd.connect()
                self.gpsconnected=True
            except:
                logging.critical('No GPS connection present. TIME NOT SET.')
                time.sleep(0.5)

    def drawfluent(self, pritext, titletext, size=_FLUENT_MED, position=(0,0)):
        if size == self._FLUENT_SMALL:
            self.drawtext(self.tiny_font, titletext, position, self._GREY)
            self.drawtext(self.sub_font, pritext, (position[0], position[1]+34), self._WHITE)
        if size == self._FLUENT_MED:
            self.drawtext(self.sub_font, titletext, position, self._GREY)
            self.drawtext(self.ui_font, pritext, (position[0], position[1]+34), self._WHITE)
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
            if self.altunit and alt_u:
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

    def formattitle(self, r, text, alt_u=None):
        try:
            if self.altunit and alt_u:
                r = r.value.to(alt_u)
                unit_shorthand = "{:~}".format(r.units)
            else:
                unit_shorthand = "{:~}".format(r.value.units)
            unit_shorthand = unit_shorthand.lower()
            unit_shorthand = unit_shorthand.replace('celsius', 'c')
            unit_shorthand = unit_shorthand.replace('fahrenheit', 'f')

            return "{0} {1}".format(text, unit_shorthand)
        except:
            return text

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

        self.setobdcommands([ obd.commands.GET_DTC ], 'dtc')
        time.sleep(2)
        r = self.connection.query(obd.commands.GET_DTC)

        if r.value:
            msg = "DTC Count {0}".format(len(r.value))
            self.infoscreen(msg, "DTCs")
            time.sleep(3)

    def draw_obd_kpi(self, obdcommand, title, location,  fontsize=_FLUENT_SMALL, alt_u=None, precision=0, titleunits=False):
        raw = self.connection.query(obdcommand)
        r = self.formatresponse(raw, precision, alt_u)
        if titleunits:
            title = self.formattitle(raw, title, alt_u)
        self.drawfluent(r, title, fontsize, location)

        return raw

    def obd_main(self):
        kpilist = [
            {'obdcommand': obd.commands.SPEED, 'title': 'speed', 'fontsize': self._FLUENT_LARGE, 'location': (260,190), 'titleunits': True, 'alt_u': 'mph'},
            {'obdcommand': obd.commands.RPM, 'title': 'rpm', 'location': (10,10) },
            {'obdcommand': obd.commands.COOLANT_TEMP, 'title': 'ect', 'fontsize': self._FLUENT_MED, 'location': (10,90), 'titleunits': True, 'alt_u': 'degF'},
            {'obdcommand': obd.commands.INTAKE_TEMP, 'title': 'iat', 'fontsize': self._FLUENT_MED, 'location': (10,220), 'titleunits': True, 'alt_u': 'degF'},
            {'obdcommand': obd.commands.THROTTLE_POS, 'title': 'tps %', 'location': (10,350) },
            {'obdcommand': obd.commands.ENGINE_LOAD, 'title': 'load %', 'location': (120,350) },
            {'obdcommand': obd.commands.TIMING_ADVANCE, 'title': 'timing', 'location': (140,10) },
            {'obdcommand': obd.commands.SHORT_FUEL_TRIM_1, 'title': 'stft1 %', 'location': (300,10) },
            {'obdcommand': obd.commands.LONG_FUEL_TRIM_1, 'title': 'ltft1 %', 'location': (420,10) },
            {'obdcommand': obd.commands.SHORT_FUEL_TRIM_2, 'title': 'stft1 %', 'location': (300,90) },
            {'obdcommand': obd.commands.LONG_FUEL_TRIM_2, 'title': 'ltft1 %', 'location': (420,90) },
        ]

        obdcommandlist = [x['obdcommand'] for x in kpilist]
        self.setobdcommands(obdcommandlist, 'main')

        try:
            self.clearscreen()

            for kpi in kpilist:
                self.draw_obd_kpi(**kpi)


        except KeyboardInterrupt:
            raise

        except:
            self.drawtext(self.ui_font, "OBD Error", (10,10))
            logging.exception('OBD Failure.. ')

        pygame.display.update()

        return self.get_pressed_keys()

    def get_pressed_keys(self):
        pygame.event.pump()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    return "K_LEFT"
                if event.key == pygame.K_RIGHT:
                    return "K_RIGHT"

        return None

    def obd_airfuel(self):
        kpilist = [
            {'obdcommand': obd.commands.MAF, 'title':"maf", 'location':(10,10), 'titleunits': True},
            {'obdcommand': obd.commands.COMMANDED_EGR, 'title':"cmd egr %", 'location':(10,90)},
            {'obdcommand': obd.commands.EGR_ERROR, 'title':'egr error %', 'location':(10,170)},
            {'obdcommand': obd.commands.INTAKE_PRESSURE, 'title':"map", 'location':(10,250), 'titleunits': True},
            {'obdcommand': obd.commands.SPEED, 'title':"speed", 'location':(10,330), 'alt_u':'mph', 'titleunits': True},
            {'obdcommand': obd.commands.RPM, 'title':"rpm", 'location':(290,330) },
            {'obdcommand': obd.commands.SHORT_FUEL_TRIM_1, 'title':"stft1", 'location':(290,10) },
            {'obdcommand': obd.commands.LONG_FUEL_TRIM_1, 'title':"ltft1", 'location':(430,10) },
            {'obdcommand': obd.commands.SHORT_FUEL_TRIM_2, 'title':"stft2", 'location':(290,90) },
            {'obdcommand': obd.commands.LONG_FUEL_TRIM_2, 'title':"ltft2", 'location':(430,90) },
            {'obdcommand': obd.commands.O2_B1S1, 'title':"o2b1s1", 'location':(290,170), 'precision':2 },
            {'obdcommand': obd.commands.O2_B1S2, 'title':"o2b1s2", 'location':(430,170), 'precision':2 },
            {'obdcommand': obd.commands.O2_B2S1, 'title':"o2b2s1", 'location':(290,250), 'precision':2 },
            {'obdcommand': obd.commands.O2_B2S2, 'title':"o2b2s2", 'location':(430,250), 'precision':2 },
        ]

        obdcommandlist = [x['obdcommand'] for x in kpilist]
        self.setobdcommands(obdcommandlist, 'airfuel')

        try:
            self.clearscreen()

            for kpi in kpilist:
                self.draw_obd_kpi(**kpi)

        except KeyboardInterrupt:
            raise

        except:
            self.drawtext(self.ui_font, "OBD Error", (10,10))
            logging.exception('OBD Failure.. ')

        pygame.display.update()

        return self.get_pressed_keys()

    def obd_gauge(self, command, title, alt_u=None, titleunits=False, min=0, max=200, warn=135):
        cmdlist = [command]
        self.setobdcommands(cmdlist, command.name)

        try:
            self.clearscreen()

            pygame.draw.circle(self.screen, self._DARKGREY, (320,240), 240)
            pygame.draw.circle(self.screen, self._BLACK, (320,240), 210)

            kpi = {'obdcommand': command, 'title': title, 'fontsize': self._FLUENT_MED, 'location':(180,160), 'alt_u': alt_u, 'titleunits': titleunits}
            raw = self.draw_obd_kpi(**kpi)

            ratio = (raw.value.magnitude - min) / (max - min)

            start = pi*1.5 - ((2*pi) * ratio)
            end = pi*1.5

            color=self._WHITE if raw.value.magnitude < warn else self._WARNING
            moirerange=10 if ratio > 0.02 else 1

            #Draw arc multiple times - prevents moire. Stupid pygame.
            for x in range(moirerange):
                pygame.draw.arc(self.screen, color, [80, 0, 480, 480], start+(0.015*x), end, 30)


        except AttributeError:
            pass

        pygame.display.update()

        return self.get_pressed_keys()

    def gpsscreen(self):
        try:
            self.clearscreen()
            packet = gpsd.get_current()

            if packet.mode >= 2:
                r = (packet.hspeed * (ureg.meter / ureg.second)).to(ureg.kph)
                if self.altunit:
                    r=r.to('mph')
                title = "speed {:~}".format(r.units)
                self.drawfluent(int(r.magnitude), title.lower(), self._FLUENT_LARGE, (260,160) )

                r = packet.get_time(local_time=True)
                self.drawfluent(r.strftime('%a, %b %d %Y %-H:%M:%S'), "time", self._FLUENT_SMALL, (10,10) )

                r = packet.alt * ureg.meter
                if self.altunit:
                    r=r.to('ft')
                title = "altitude {:~}".format(r.units)

                self.drawfluent(int(r.magnitude), title.lower(), self._FLUENT_SMALL, (10,90) )

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
            raise

        except:
            self.drawtext(self.ui_font, "GPS Error", (10,10))
            logging.exception('GPS Failure.. ')

        pygame.display.update()

        return self.get_pressed_keys()


    def accelerometer(self, ax, ay, maxax, maxay):
        try:
            at = hypot(ax, ay)
        except:
            at=0
        try:
            mat = hypot(maxax, maxay)
        except:
            mat=0

        self.clearscreen()

        pygame.draw.circle(self.screen, self._WHITE, (320,240), 230)
        pygame.draw.circle(self.screen, self._BLACK, (320,240), 210)

        pygame.draw.circle(self.screen, self._GREY, (320,240), 169)
        pygame.draw.circle(self.screen, self._BLACK, (320,240), 167)

        pygame.draw.circle(self.screen, self._WHITE, (320,240), 7)

        dy = int((ay / 1.25) * 210)
        dx = int((ax / 1.25) * 210)

        if ay >= 0:
            meatball_color = ( min( abs(int((ay / 1.25) * 255)), 255), 0, 0)
        else:
            meatball_color = ( 0, min( abs(int((ay / 1.25) * 255)), 255) , 0)

        try:
            pygame.draw.circle(self.screen, self._WHITE, (320+dx,240-dy), 15)
            pygame.draw.circle(self.screen, meatball_color, (320+dx,240-dy), 12)
        except:
            logging.exception(meatball_color)


        self.drawfluent('{:0.2f}'.format(ay), 'accel g', self._FLUENT_SMALL, (10,10) )
        self.drawfluent('{:0.2f}'.format(ax), 'lat g', self._FLUENT_SMALL, (10,380) )
        self.drawfluent('{:0.2f}'.format(at), 'tot g', self._FLUENT_SMALL, (540,10) )
        self.drawfluent('{:0.2f}'.format(mat), 'max g', self._FLUENT_SMALL, (540,380) )

        pygame.display.update()

        time.sleep(0.06)

        return self.get_pressed_keys()

