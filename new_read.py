#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

print("Card Scanning")
print("To cancel press ctrl+c")

try:
    while True:
        id, text = reader.read()
        print("Card label: " + text)
        print("Card UID: " + str(id))
        time.sleep(3)
      
finally:
    GPIO.cleanup()
    