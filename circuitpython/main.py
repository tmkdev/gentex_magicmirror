import time
import board
import busio
import adafruit_dotstar
import analogio
import digitalio
import adafruit_bno055

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

led.value = False
brightness=32

pin = analogio.AnalogIn(board.A3)
pixels = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)

i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
sensor = adafruit_bno055.BNO055(i2c, 0x29)
sensor.mode = adafruit_bno055.NDOF_FMC_OFF_MODE 

led.value = True

while True:
    (x,y,z) = sensor.linear_acceleration

    #print('Magnetometer (microteslas): {}'.format(sensor.magnetometer))
    #print('Gyroscope (deg/sec): {}'.format(sensor.gyroscope))
    #print('Euler angle: {}'.format(sensor.euler))
    #print('Quaternion: {}'.format(sensor.quaternion))

    print("AX:{:.2f}".format(x/9.81))
    print("AY:{:.2f}".format(y/9.81))
    print("AZ:{:.2f}".format(z/9.81))

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

    time.sleep(0.025)
