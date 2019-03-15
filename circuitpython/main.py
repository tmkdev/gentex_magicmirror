import analogio
from board import *
import time

pin = analogio.AnalogIn(A0)

while True:
	pinvalue = pin.value
	if pinvalue < 9000:
		print("BTNS:0")
	elif pinvalue >= 9000 and pinvalue < 20000:
		print("BTNS:1")
	elif pinvalue >= 20000 and pinvalue < 40000:
		print("BTNS:2")
	elif pinvalue > 40000:
		print("BTNS:3")

	time.sleep(0.05)
