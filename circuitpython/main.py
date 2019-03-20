import time
import board
import busio
import adafruit_adxl34x
import adafruit_dotstar
import analogio
import digitalio

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

led.value = False

pin = analogio.AnalogIn(board.A3)

brightness=16

pixels = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)

i2c = busio.I2C(board.SCL, board.SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

xa = []
ya = []
za = []

for x in range(10):
    (x,y,z) = accelerometer.acceleration
    xa.append(x)
    ya.append(y)
    za.append(z)
    time.sleep(0.05)

calx = -(sum(xa) / 10.0)
caly = -(sum(ya) / 10.0)
calz = 9.81 - (sum(za) / 10.0)

led.value = True

print("CALX:{:.2f}".format(calx))
print("CALY:{:.2f}".format(caly))
print("CALZ:{:.2f}".format(calz))

while True:
    (x,y,z) = accelerometer.acceleration

    x += calx
    y += caly
    z += calz

    print("AX:{:.2f}".format(x))
    print("AY:{:.2f}".format(y))
    print("AZ:{:.2f}".format(z))

    pinvalue = pin.value
    if pinvalue < 9000:
        print("BTNS:0")
        pixels[0] = (brightness, brightness, 0)
    elif pinvalue >= 9000 and pinvalue < 20000:
        print("BTNS:1")
        pixels[0] = (0, brightness, 0)
    elif pinvalue >= 20000 and pinvalue < 40000:
        print("BTNS:2")
        pixels[0] = (0, 0, brightness)
    elif pinvalue > 40000:
        print("BTNS:3")
        pixels[0] = (brightness, 0, 0)

    time.sleep(0.05)
