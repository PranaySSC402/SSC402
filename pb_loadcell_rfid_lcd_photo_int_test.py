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

#led modules start
#import board
#import neopixel
#led modules end

#line 13 is database connector
import mysql.connector

# image and others
import os
import cv2
import numpy as np
from PIL import Image
from tensorflow import keras
from picamera import PiCamera

#the following line creates a variable to connect the database to be used with the code
db = mysql.connector.connect(host="localhost", user="crdadm", passwd="4301DB", database="creditsystem")

#the following line creates a variable to allow for the reading of the rfid tags
reader = SimpleMFRC522()

#the following line creates a way for information from the code to be stored into the database
cursor = db.cursor(buffered=True)

#counter to not calibrate weight all the time
cnt = 0

# imaging function
param_C = 2
threshold = 0.9
sigma_space = 75
sigma_color = 75
pixel_diameter = 11
param_blockSize = 21
close_kernel = np.ones((2, 2), np.uint8)
dilate_kernel = np.ones((2, 2), np.uint8)
param_thresholdType = cv2.THRESH_BINARY_INV
param_adaptiveMethod = cv2.ADAPTIVE_THRESH_MEAN_C

model = keras.models.load_model('trained_model')

def picamera_photo():
    camera = PiCamera()
    camera.rotation = 90
    camera.resolution = (1920, 1080)
    time.sleep(2)
    camera.capture('/home/ssc402/Desktop/Test.jpg')
    camera.close()
    return np.array(Image.open('/home/ssc402/Desktop/Test.jpg').convert("L"))

def pet_prediction(image_x):
    sample_x = image_x[275:805, 95:1465]
    bilateralf_img = cv2.bilateralFilter(sample_x, pixel_diameter, sigma_space, sigma_color, borderType = cv2.BORDER_DEFAULT)
    bilateralf_at_img = cv2.adaptiveThreshold(bilateralf_img, bilateralf_img.max(), param_adaptiveMethod, param_thresholdType, param_blockSize, param_C)
    opening = cv2.morphologyEx(bilateralf_at_img, cv2.MORPH_CLOSE, close_kernel, iterations = 30)
    sure_bg = cv2.dilate(opening, dilate_kernel, iterations = 10)
    processed_x = (np.array(sure_bg) / 255.0).reshape(-1, 530, 1370, 1)
    prediction = model.predict(processed_x, verbose = 0)[0][0] > threshold
    return prediction

def empty_prediction(weight):
    if 10 <= abs(weight) < 90:
        prediction = 1
    else:
        prediction = 0
    return prediction

def image_process():
    num = 0
    image_x = img_array[num]
    pet_pred = pet_prediction(image_x)
    weight_info = 30
    empty_pred = empty_prediction(weight_info)
    return((not pet_pred) or (not empty_pred))

def arduino_message(instruct):
    if instruct == 'spin':
        print(instruct)
    elif instruct == 'spin&drop':
        print(instruct)
    else:
        print(instruct)


try:
    while True:
        
        #LED: Idle state
    #    pixels1.fill((0, 0, 255)) #blue in idle state # comment this line out if the function doesn't work
    
        #LCD Message 1: Played when bin is in idle state
        lcd.cursor_pos = (0, 5)
        lcd.write_string('Please tap')
        lcd.cursor_pos = (1, 2)
        lcd.write_string('your NUS student')
        lcd.cursor_pos = (2, 2)
        lcd.write_string('or staff card to')
        lcd.cursor_pos = (3, 2)
        lcd.write_string('begin recycling')
        
        #id: rfid tag number, text: Name associated to each tag
        id, text = reader.read()
        lcd.clear()
        print(id)
        print(text)
        
        #LED: Insertion state
       # pixels1.fill((0, 255, 0)) #green in bottle insertion state # comment this line out if the function doesn't work
        
        #Assign lcd_name = text + '                                        '
        #to ensure that lcd_name will have at least 40 characters to be printed in the middle 2 lines
        lcd_name = text + '                                        '
        lcd.cursor_pos = (0, 0)
        lcd.write_string('Hello ' + lcd_name[0:14])
        lcd.cursor_pos = (1, 0)
        lcd.write_string(lcd_name[14:34])
        lcd.cursor_pos = (2, 0)
        lcd.write_string('-Welcome to our bin!')
        time.sleep(2)
        
        lcd.clear()
        #LCD Message 3: Played to prompt user to open the flap to insert empty PET bottle in the bin
        lcd.cursor_pos = (0, 0)
        lcd.write_string('Raise the flap to')
        lcd.cursor_pos = (1, 0)
        lcd.write_string('insert an empty PET')
        lcd.cursor_pos = (2, 0)
        lcd.write_string('bottle into the bin')
        lcd.cursor_pos = (3, 0)
        lcd.write_string('& press the button!')
        
        #BUTTON should be pushed here by user
#       *********************************************************************

#         input()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(37, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Set pin 17 as input with pull-up resistor
        
        pb = GPIO.wait_for_edge(37, GPIO.FALLING, timeout = 10000)
        
        if pb is None:
            print('Timeout occured! Executing machine commands anyway.')
            #LCD Message 4: Played once bottle has been inserted AND button has been pressed by user
            lcd.clear()
            lcd.cursor_pos = (0, 3)
            lcd.write_string('Thank you! You')
            lcd.cursor_pos = (1, 3)
            lcd.write_string('may leave now!')
            lcd.cursor_pos = (2, 0)
            lcd.write_string('Have a splendid day!')
            #LED: Processing state
            #pixels1.fill((255, 0, 0)) #red in DO NOT INSERT state # comment this line out if the function doesn't work

        
        else:
            print("Button pressed! Executing machine commands!")
            #LCD Message 4: Played once bottle has been inserted AND button has been pressed by user
            lcd.clear()
            lcd.cursor_pos = (0, 3)
            lcd.write_string('Thank you! You')
            lcd.cursor_pos = (1, 3)
            lcd.write_string('may leave now!')
            lcd.cursor_pos = (2, 0)
            lcd.write_string('Have a splendid day!')
            #LED: Processing state
         #   pixels1.fill((255, 0, 0)) #red in DO NOT INSERT state # comment this line out if the function doesn't work

        #time.sleep(3)
        #to trigger the completion of the insertion of the bottle
#       *********************************************************************
        
        st = time.time()
        #time.sleep(3)
        #to trigger the completion of the insertion of the bottle
        arduino_message('spin')     # chamber 1 -> 2
        
        #LCD Message 4: Played once bottle has been inserted AND button has been pressed by user
        lcd.clear()
        lcd.cursor_pos = (0, 1)
        lcd.write_string('Thank you! You')
        lcd.cursor_pos = (1, 1)
        lcd.write_string('may leave now!')
        
        #Lines 64 & 65 will be here temporarily. 64: Check for image, 65: Check weight
        # p = int(input("Is the object a PET bottle? 1:Yes 0:No \n"))
        # take photo
        st1 = time.time()
        image_x = picamera_photo()
        print("PHOTO TAKEN")
    
        ed1 = time.time()
        print('PHOTO TIME: ' + str(ed1 - st1))

        #e = int(input("Does the object meet the empty PET bottle weight requirement? 1:Yes 0:No \n"))
        
        
        #Initialising the e value, weight part of the code
        #*******************************************************************************************************

        st1 = time.time()
        EMULATE_HX711=False

        referenceUnit = 403

        hx = HX711(29, 31)

        hx.set_reading_format("MSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.

        hx.set_reference_unit(referenceUnit) #commented out based on instructions on tutorial

        hx.reset()

        print("START TARE")
        hx.tare()

        print("Tare done! Add weight now...")
        arduino_message('spin')     # chamber 2 -> 3
        time.sleep(1) # time for spinning to take place

        val = hx.get_weight(5)
        #store += val
        print(abs(val))

        hx.power_down()
        hx.power_up()
        time.sleep(0.1)

        ed1 = time.time()
        print('WEIGHING TIME: ' + str(ed1 - st1))
        
#mean = store/2000
#print('Avg of 2000 weight vals = ' + str(mean))
        
        e = empty_prediction(val)
        arduino_message('spin')     # chamber 3 -> 4
        
        #*******************************************************************************************************

        st1 = time.time()
        p = int(pet_prediction(image_x))
        ed1 = time.time()
        print('PREDICTION TIME: ' + str(ed1 - st1))
        print("IMAGE PROCESSED")
        arduino_message('spin')     # chamber 4 -> 5
        
        arduino_message('spin')     # chamber 5 -> 6
        
        #lines 68-71 make a decision on if credit should be given or not
        if p == 1 and e == 1:
            c = 1
            arduino_message('spin')     # chamber 6 -> 7
        else:
            c = 0
            arduino_message('spin&drop')     # chamber 6 -> 7

        st1 = time.time()
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

        print("DATABASE UPDATED")
        ed1 = time.time()
        print('DATABASE TIME: ' + str(ed1 - st1))        

        arduino_message('spin')     # chamber 7 -> 8
        
        # time.sleep(3)
        #This lcd clearing function may have to be placed elsewhere upon deeper integration
        lcd.clear()
        
        ed = time.time()
        print('SINGLE CYCLE TIME: ' + str(ed - st))
      
finally:
    GPIO.cleanup()
    
    
    
#from hello_world import c
#import os
#print(c)
