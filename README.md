# gentex_magicmirror
Raspberry Pi to Gentex 657 rear view (LCD) magic mirror 

Open font source:
https://github.com/winjs/winstrap/tree/5a3c1341190e7585fd550e01cfded50ae4e8a4c7/src/fonts 

pygame code based on:
https://learn.adafruit.com/pi-video-output-using-pygame/pointing-pygame-to-the-framebuffer 


Notes on the Gentex 657 mirror.
Driving reverse lamp pin (9) with a duty cycle of 10s on, 1s off keeps it from timing out. It works as low as 3.3V, driven from a raspberry pi GPIO. 

Mirror Pinout: https://ls1tech.com/forums/stereo-electronics/1887542-need-pinout-16-pin-mirror-camera-display.html#&gid=1&pid=1 

Possible pins for the connector: https://www.mouser.com/ProductDetail/TE-Connectivity-AMP/175265-1?qs=AplfTeSvkkBL3BcjZdHR5Q%3D%3D
Possible Mating connector: https://www.mouser.com/datasheet/2/418/NG_CD_179054_O-659708.pdf

Example of the thing runing: https://photos.app.goo.gl/M7oZyTBy9QhEEuzM9 

![Alt text](assets/screenshots/gps_screen.jpg?raw=true "GPS Screenshot")
![Alt text](assets/screenshots/obd_screen.jpg?raw=true "OBD Screenshot")
![Alt text](assets/screenshots/airfuel_screen.jpg?raw=true "AirFuel Screenshot")
