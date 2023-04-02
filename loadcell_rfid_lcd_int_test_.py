#!/usr/bin/env python
#lines 3-5 are rfid part imports
import RPi.GPIO as GPIO
import time
from mfrc522 import SimpleMFRC522

#lines 8-10 are lcd part imports
from RPLCD import *
from RPLCD.i2c import CharLCD
lcd = CharLCD('PCF8574', 0x27)

#load cell packages
import sys
from hx711 import HX711

#line 13 is database connector
import mysql.connector

#the following line creates a variable to connect the database to be used with the code
db = mysql.connector.connect(host="localhost", user="crdadm", passwd="4301DB", database="creditsystem")

#the following line creates a variable to allow for the reading of the rfid tags
reader = SimpleMFRC522()

#the following line creates a way for information from the code to be stored into the database
cursor = db.cursor(buffered=True)

#counter to not calibrate weight all the time
cnt = 0

try:
    while True:
        #LCD Message 1: Played when bin is in idle state
        lcd.cursor_pos = (0, 0)
        lcd.write_string('Please scan your')
        lcd.cursor_pos = (1, 1)
        lcd.write_string('card to begin.')
        
        #id: rfid tag number, text: Name associated to each tag
        id, text = reader.read()
        lcd.clear()
        print(id)
        print(text)
        
        #LCD Message 2: Played once user scans card
        lcd.cursor_pos = (0, 4)
        lcd.write_string('Welcome,')
        lcd.cursor_pos = (1, 3)
        lcd.write_string('to our bin')
        time.sleep(2)
        
        #LCD Message 3: Played to prompt user to insert empty PET bottle in the bin
        lcd.cursor_pos = (0, 0)
        lcd.write_string('Please insert an')
        lcd.cursor_pos = (1, 0)
        lcd.write_string('empty PET bottle')
        
        #BUTTON should be pushed here by user
#       *********************************************************************
        input()
        #time.sleep(3)
        #to trigger the completion of the insertion of the bottle
        
        #LCD Message 4: Played once bottle has been inserted AND button has been pressed by user
        lcd.clear()
        lcd.cursor_pos = (0, 1)
        lcd.write_string('Thank you! You')
        lcd.cursor_pos = (1, 1)
        lcd.write_string('may leave now!')
        
        #Lines 64 & 65 will be here temporarily. 64: Check for image, 65: Check weight
        p = int(input("Is the object a PET bottle? 1:Yes 0:No \n"))
        #e = int(input("Does the object meet the empty PET bottle weight requirement? 1:Yes 0:No \n"))
        
        
        #Initialising the e value, weight part of the code
        #*******************************************************************************************************
#         import time

        st = time.time()

        EMULATE_HX711=False

        referenceUnit = 403

#         if not EMULATE_HX711:
#             import RPi.GPIO as GPIO
#             from hx711 import HX711
#         else:
#             from emulated_hx711 import HX711

#         def cleanAndExit():
#             print("Cleaning...")
# 
#             if not EMULATE_HX711:
#                 GPIO.cleanup()
#         
#             print("Bye!")
#             sys.exit()

        hx = HX711(29, 31)

        hx.set_reading_format("MSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.

        hx.set_reference_unit(referenceUnit) #commented out based on instructions on tutorial

        hx.reset()

        hx.tare()

        print("Tare done! Add weight now...")
        time.sleep(2)

        val = hx.get_weight(5)
        #store += val
        print(val)

        ed = time.time()
        print('tare 1 time: ' + str(ed - st))

        hx.power_down()
        hx.power_up()
        time.sleep(0.1)
        
#mean = store/2000
#print('Avg of 2000 weight vals = ' + str(mean))
        
        if 15 <= val <= 35:
            e = 1
        else:
            e = 0
        
        #*******************************************************************************************************
        
        
        #lines 68-71 make a decision on if credit should be given or not
        if p == 1 and e == 1:
            c = 1
        else:
            c = 0
            
        #76: From predefi table in Database
        #if RFID_tag_no header value is the same as id varin this code,
        #then select RFID_tag_no, Name and NUS_email in the same row
        cursor.execute("SELECT RFID_tag_no, Name FROM predefi WHERE RFID_tag_no="+str(id))
        #78: Store the aforementioned values into an array called result
        result = cursor.fetchone()
        
        #cursor.rowcount shows how many rows are being queried from the table in the database
        if cursor.rowcount >= 1:
            #enter details of the card tap from the query into a table
            #to record if user has recycled properly
            cursor.execute("INSERT INTO card_tap (RFID_tag_no, PET_bottle, Empty, Credit) VALUES (%s, %s, %s, %s)", (result[0], p, e, c))
            
            #user who has just tapped card has been recorded to recycle and empty PET bottle
            if c == 1:
                #update points table for user whose Name in the table is equal to text var
                #add c var to the points in the table
                cursor.execute("UPDATE predefi SET Points = Points + (%s) WHERE Name = (%s)", (c, text)) 
            
            db.commit()
            
        time.sleep(3)
        #This lcd clearing function may have to be placed elsewhere upon deeper integration
        lcd.clear()
      
finally:
    GPIO.cleanup()
    
    
    
#from hello_world import c
#import os
#print(c)