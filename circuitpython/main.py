import analogio
from board import *
import time
import adafruit_dotstar

pin = analogio.AnalogIn(A0)


pixels = adafruit_dotstar.DotStar(APA102_SCK, APA102_MOSI, 1)

while True:
	pinvalue = pin.value
	if pinvalue < 9000:
		print("BTNS:0")
		pixels[0] = (128, 128, 0)
	elif pinvalue >= 9000 and pinvalue < 20000:
		print("BTNS:1")
		pixels[0] = (0, 255, 0)
	elif pinvalue >= 20000 and pinvalue < 40000:
		print("BTNS:2")
		pixels[0] = (0, 0, 255)
	elif pinvalue > 40000:
		print("BTNS:3")
		pixels[0] = (255, 0, 0)

	time.sleep(0.05)
