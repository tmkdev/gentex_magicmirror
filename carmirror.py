import os
import pygame
import time
import random
import pygame.freetype
import gpsd
import logging

from gpiozero import LED
from signal import pause

red = LED(17)

red.blink(on_time=10, off_time=1, background=True)


class carmirror(object):
    screen = None


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
        self.tiny_font = pygame.font.Font("segoeuil.ttf", 32)
        # Render the screen
        pygame.mouse.set_visible(False)
        pygame.display.update()


    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def drawtext(self, font, text, position, color=(255,255,255)):
        text = font.render(str(text), True, color)
        self.screen.blit(text, position)

    def clearscreen(self):
        black = (0, 0, 0)
        self.screen.fill(black)

    def test(self):
        connected = False
        mpstokph = 3.6

        while not connected:
            try:
                gpsd.connect()
                connected=True
            except:
                logging.critical('No GPS connection present. TIME NOT SET.')
                time.sleep(0.5)

        while True:
            try:
                self.clearscreen()
                packet = gpsd.get_current()

                if packet.mode >= 2:
                    self.drawtext(self.huge_font, int(packet.hspeed), (320,110))
                    self.drawtext(self.tiny_font, "Speed(mph)", (350,120), (128,128,128))
                    self.drawtext(self.tiny_font, packet.time, (20,40))
                    self.drawtext(self.tiny_font, "Time", (20,10), (128,128,128))
                    self.drawtext(self.ui_font, packet.alt, (10,210))
                    self.drawtext(self.tiny_font, "Altitude", (20,200), (128,128,128))
                    self.drawtext(self.ui_font, packet.track, (10,310))
                    self.drawtext(self.tiny_font, "Heading", (20,300), (128,128,128))
                    self.drawtext(self.tiny_font, packet.lat, (20,420))
                    self.drawtext(self.tiny_font, packet.lon, (340,420))

                else:
                    self.drawtext(self.ui_font, "No GPS", (10,10))

            except KeyboardInterrupt:
                break

            except:
                self.drawtext(self.ui_font, "GPS Error", (10,10))
                logging.exception('GPS Failure.. ')

            pygame.display.update()


# Create an instance of the PyScope class
scope = carmirror()
scope.test()

