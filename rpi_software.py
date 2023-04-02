#!/usr/bin/env python

import os
import cv2
import sys
import time
import serial
import numpy as np
import func_timeout
from RPLCD import *
from PIL import Image
import mysql.connector
import RPi.GPIO as GPIO
from hx711 import HX711
from tensorflow import keras
from RPLCD.i2c import CharLCD
from picamera import PiCamera
from mfrc522 import SimpleMFRC522

param_C = 2
sigma_space = 75
sigma_color = 75
pixel_diameter = 11
param_blockSize = 21
close_kernel = np.ones((2, 2), np.uint8)
dilate_kernel = np.ones((2, 2), np.uint8)
param_thresholdType = cv2.THRESH_BINARY_INV
param_adaptiveMethod = cv2.ADAPTIVE_THRESH_MEAN_C

reader = SimpleMFRC522()
lcd = CharLCD('PCF8574', 0x27)
db = mysql.connector.connect(host="localhost", user="crdadm", passwd="4301DB", database="creditsystem")
cursor = db.cursor(buffered=True)

referenceUnit = 410
hx = HX711(29, 31)

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.reset_input_buffer()

print("Model Loading ...")
model = keras.models.load_model('trained_model')
print("Model Loaded")

def press_btn():
    print('PRESS BUTTON')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(37, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    pb = GPIO.wait_for_edge(37, GPIO.FALLING, timeout = 20000)

def user_setup():
    global reader, lcd
    
    lcd.clear()
    lcd.cursor_pos = (0, 5)
    lcd.write_string('Please tap')
    lcd.cursor_pos = (1, 2)
    lcd.write_string('your NUS student')
    lcd.cursor_pos = (2, 2)
    lcd.write_string('or staff card to')
    lcd.cursor_pos = (3, 2)
    lcd.write_string('begin recycling')
        
    id, text = reader.read()
    
    lcd.clear()
    
    lcd_name = text + '                                        '
    lcd.cursor_pos = (0, 0)
    lcd.write_string('Hello ' + lcd_name[0:14])
    lcd.cursor_pos = (1, 0)
    lcd.write_string(lcd_name[14:34])
    lcd.cursor_pos = (2, 0)
    lcd.write_string('-Welcome to our bin!')
    arduino_message('welcoming')
    
    time.sleep(1)
    lcd.clear()
        
    lcd.cursor_pos = (0, 2)
    lcd.write_string('Lift the flap to')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('insert an empty PET')
    lcd.cursor_pos = (2, 0)
    lcd.write_string('bottle into the bin')
    lcd.cursor_pos = (3, 0)
    lcd.write_string('& press the button!')

    try:
        func_timeout.func_timeout(20, press_btn, args=[])
    except func_timeout.FunctionTimedOut:
        pass
    arduino_message('processing')
    
    lcd.clear()
    lcd.cursor_pos = (0, 5)
    lcd.write_string('Thank you!')
    lcd.cursor_pos = (1, 1)
    lcd.write_string('You may leave now!')
    lcd.cursor_pos = (2, 0)
    lcd.write_string('Have a splendid day!')
    lcd.cursor_pos = (3, 1)
    lcd.write_string('Please come again!')

    return (id, text)

def arduino_message(instruct):
    global ser
    if instruct == 'spining':
        print(instruct)
        ser.write(b'1')
    elif instruct == 'spin&droping':
        print(instruct)
        ser.write(b'2')
    elif instruct == 'welcoming':
        print(instruct)
        ser.write(b'3')
    elif instruct == 'processing':
        print(instruct)
        ser.write(b'4')
    elif instruct == 'ready':
        print(instruct)
        ser.write(b'5')
    elif instruct == 'imaging':
        print(instruct)
        ser.write(b'6')
    else:
        print(instruct)
        ser.write(b'0')
    line = ser.readline().decode('utf-8').rstrip()
    print(line)
    time.sleep(1)

def picamera_photo():
    camera = PiCamera()
    camera.rotation = 90
    camera.resolution = (1920, 1080)
    arduino_message('imaging')
    time.sleep(2)
    camera.capture('/home/ssc402/Desktop/Test.jpg')
    camera.close()
    return np.array(Image.open('/home/ssc402/Desktop/Test.jpg').convert("L"))

def weigh_taring():
    global hx
    hx.set_reading_format("MSB", "MSB")
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    hx.tare()

def weighing_prediction():
    global hx
    time.sleep(1)
    val = abs(hx.get_weight(5))
    print(val)
    hx.power_down()
    hx.power_up()
    time.sleep(0.1)
    return empty_prediction(val)

def empty_prediction(weight):
    if 10 <= weight < 90:
        prediction = 1
    else:
        prediction = 0
    print('Weighing result: ' + str(prediction))
    return prediction

def pet_prediction(image_x):
    sample_x = image_x[200:950, 50:1850]
    bilateralf_img = cv2.bilateralFilter(sample_x, pixel_diameter, sigma_space, sigma_color, borderType = cv2.BORDER_DEFAULT)
    bilateralf_at_img = cv2.adaptiveThreshold(bilateralf_img, bilateralf_img.max(), param_adaptiveMethod, param_thresholdType, param_blockSize, param_C)
    opening = cv2.morphologyEx(bilateralf_at_img, cv2.MORPH_CLOSE, close_kernel, iterations = 30)
    sure_bg = cv2.dilate(opening, dilate_kernel, iterations = 10)
    resized = cv2.resize(sure_bg, dsize=(1370, 530), interpolation=cv2.INTER_NEAREST)
    processed_x = (np.array(resized) / 255.0).reshape(-1, 530, 1370, 1)
    prediction = model.predict(processed_x, verbose = 0)[0][0] >= 1.0
    print('Imaging result: ' + str(prediction))
    return int(prediction)

def database_update(rfid_tag, name, pet, empty):
    global cursor, db
    if pet == 1 and empty == 1:
        credit = 1
        arduino_message('spining')  # chamber 6 -> 7
    else:
        credit = 0
        arduino_message('spin&droping')     # chamber 6 -> 7
        
    cursor.execute("SELECT RFID_tag_no, Name FROM predefi WHERE RFID_tag_no="+str(rfid_tag))
    result = cursor.fetchone() 
    if cursor.rowcount >= 1:
        cursor.execute("INSERT INTO card_tap (RFID_tag_no, PET_bottle, Empty, Credit) VALUES (%s, %s, %s, %s)", (result[0], pet, empty, credit))
        if credit == 1:
            cursor.execute("UPDATE predefi SET Points = Points + (%s) WHERE Name = (%s)", (credit, name))     
        db.commit()

if __name__ == '__main__':
    weigh_taring()
    arduino_message('ready')
    try:
        while True:
            # Chamber 1
            (rfid_tag, name) = user_setup()
            arduino_message('spining')
            st_all = time.time()

            # Chamber 2
            st_short = time.time()
            image_x = picamera_photo()
            ed_short = time.time()
            print('PHOTO TIME: ' + str(ed_short - st_short))
            arduino_message('spining')

            # Chamber 3
            st_short = time.time()
            e = weighing_prediction()
            ed_short = time.time()
            print('WEIGHING TIME: ' + str(ed_short - st_short))
            arduino_message('spining')
            
            # Chamber 4-5
            st_short = time.time()
            p = pet_prediction(image_x)
            ed_short = time.time()
            print('PREDICTION TIME: ' + str(ed_short - st_short))
            arduino_message('spining')
            arduino_message('spining')

            # Chamber 6-7-8
            st_short = time.time()
            database_update(rfid_tag, name, p, e)
            ed_short = time.time()
            print('DATABASE UPDATED: ' + str(ed_short - st_short))
            arduino_message('spining')
            lcd.clear()
            ed_all = time.time()
            print('SINGLE CYCLE TIME: ' + str(ed_all - st_all))
            arduino_message('ready')
          
    finally:
        GPIO.cleanup()
