# gentex_magicmirror
## ELM327 Switched 12V Mod
---
I am using a usb->elm327 to gather OBD2 info. Worried that it would be constantly connected to 12V on OBD pin 16, I decided to add a relay to my dongle to switch 12V. Should keep the battery nice and charged. 

## Step 1 
Cut the 12V pin to the motherboard. Relay normally open contacts will be wired between. Use a multimeter to scope out where the pin is. Most of these dongles are similar inside. 
![Alt text](assets/elm_modifications/cut_12V_pin.jpg?raw=true "12V pin cut.")

## Step 2 
Find power. I could have used the 5V/GND pins from the USB header. I only had a 3V relay handy and my board had a nice pad for GND and 3.3V. So... Connect the power to the coil. When the ELM gets USB power, coil closes - 12V flows. 
![Alt text](assets/elm_modifications/3_3V_source_for_relay.jpg?raw=true "3.3V power for coil.")

## Step 3 
Complete the wiring. Hot glue everything in. (Or whatever.)
![Alt text](assets/elm_modifications/relay_installed.jpg?raw=true "Relay Installed")

## 2 Way Video Switcher
---
2 way video swich for backup camera: https://www.ebay.com/itm/FPV-Multi-camera-Mini-Two-way-Electronic-Switch-Video-Switcher-Module-for-RC-Dro/173818046132?epid=1463144405&hash=item28785ce6b4:g:5NAAAOSw-K1cefKV 


## Trinket M0 Gentex Analog Interface and Accelerometer
---
[Trinket M0](https://learn.adafruit.com/adafruit-trinket-m0-circuitpython-arduino/overview) from [Adafruit](https://adafruit.com)

GY-BNO055 9 Axis Orientation Sensor

Code in the circuit python folder. 

Need an arduino to read the resistor ladder buttons in the mirror. They actually work fine at 3.3V, and the Leds light dimly. The arduino also emits the linear acceleration and euler angles from a BNO-055. 

### ToDo: 
- [ ] Schematic