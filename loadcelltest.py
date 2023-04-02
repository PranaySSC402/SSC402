import RPi.GPIO as GPIO
from hx711 import HX711
import time

referenceUnit = 410
hx = HX711(29, 31)


hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()

while True:
    val = abs(hx.get_weight(5))
    print(val)
    hx.power_down()
    hx.power_up()
    time.sleep(0.1)
    