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
threshold = 0.9
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

chambers = [0, 0, 0, 0, 0, 0, 0, 0]
ids = []
names = []
multi_in = False
object_images = []
pet_pred = []
empty_pred = []

print("Model Loading ...")
model = keras.models.load_model('trained_model')
print("Model Loaded")


def scan_id():
    global ids, names, chambers
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
    ids.append(id)
    names.append(text)
    chambers.append(1)
    
    lcd_name = text + '                                        '
    lcd.cursor_pos = (0, 0)
    lcd.write_string('Hello ' + lcd_name[0:14])
    lcd.cursor_pos = (1, 0)
    lcd.write_string(lcd_name[14:34])
    lcd.cursor_pos = (2, 0)
    lcd.write_string('-Welcome to our bin!')
    time.sleep(1)
        
    lcd.cursor_pos = (0, 0)
    lcd.write_string('Raise the flap to')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('insert an empty PET')
    lcd.cursor_pos = (2, 0)
    lcd.write_string('bottle into the bin')
    lcd.cursor_pos = (3, 0)
    lcd.write_string('& press the button!')

def press_btn():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(37, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    pb = GPIO.wait_for_edge(37, GPIO.FALLING, timeout = 20000)

def next_item():
    global lcd, multi_in

    lcd.clear()
    lcd.cursor_pos = (0, 2)
    lcd.write_string('If you have more')
    lcd.cursor_pos = (1, 1)
    lcd.write_string('empty PET bottles,')
    lcd.cursor_pos = (2, 0)
    lcd.write_string('press the button now')
    
    press_btn()
    multi_in = True

def enter_item():
    global lcd
    try:
        func_timeout.func_timeout(20, press_btn, args=[])
    except func_timeout.FunctionTimedOut:
        pass
    
    arduino_message('processing')
    # arduino_message('next item')

    try:
        func_timeout.func_timeout(10, next_item, args=[])
    except func_timeout.FunctionTimedOut:
        pass
    
    arduino_message('processing')
    
    lcd.clear()
    if multi_in == False:
        lcd.cursor_pos = (0, 5)
        lcd.write_string('Thank you!')
        lcd.cursor_pos = (1, 1)
        lcd.write_string('You may leave now!')
        lcd.cursor_pos = (2, 0)
        lcd.write_string('Have a splendid day!')
        lcd.cursor_pos = (3, 1)
        lcd.write_string('Please come again!')
    else:
        lcd.cursor_pos = (0, 0)
        lcd.write_string('********************')
        lcd.cursor_pos = (1, 2)
        lcd.write_string('...Processing...')
        lcd.cursor_pos = (2, 3)
        lcd.write_string('PLEASE WAIT...')
        lcd.cursor_pos = (3, 0)
        lcd.write_string('********************')

def user_setup():
    global ids, names, lcd, chambers, multi_in
    
    if multi_in:
        multi_in = False
        
        lcd.cursor_pos = (0, 0)
        lcd.write_string('Raise the flap to')
        lcd.cursor_pos = (1, 0)
        lcd.write_string('insert an empty PET')
        lcd.cursor_pos = (2, 0)
        lcd.write_string('bottle into the bin')
        lcd.cursor_pos = (3, 0)
        lcd.write_string('& press the button!')

        ids.append(ids[-1])
        names.append(names[-1])
        chambers.append(1)
        enter_item()
    else:
        if chambers.count(1) == 0:
            scan_id()
            enter_item()
        else:
            try:
                func_timeout.func_timeout(5, scan_id, args=[])
                enter_item()
            except func_timeout.FunctionTimedOut:
                pass

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
    global object_images
    camera = PiCamera()
    camera.rotation = 90
    camera.resolution = (1920, 1080)
    arduino_message('imaging')
    time.sleep(2)
    camera.capture('/home/ssc402/Desktop/Test.jpg')
    camera.close()
    object_images.append(np.array(Image.open('/home/ssc402/Desktop/Test.jpg').convert("L")))

def weigh_taring():
    global hx
    hx.set_reading_format("MSB", "MSB")
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    hx.tare()

def weighing_prediction():
    global empty_pred, hx
    val = abs(hx.get_weight(5))
    hx.power_down()
    hx.power_up()
    time.sleep(0.1)
    empty_pred.append(empty_prediction(val))

def empty_prediction(weight):
    if 10 <= weight < 90:
        prediction = 1
    else:
        prediction = 0
    return prediction

def pet_prediction():
    global object_images, pet_pred
    image_x = object_images[0]
    sample_x = image_x[200:950, 50:1850]
    bilateralf_img = cv2.bilateralFilter(sample_x, pixel_diameter, sigma_space, sigma_color, borderType = cv2.BORDER_DEFAULT)
    bilateralf_at_img = cv2.adaptiveThreshold(bilateralf_img, bilateralf_img.max(), param_adaptiveMethod, param_thresholdType, param_blockSize, param_C)
    opening = cv2.morphologyEx(bilateralf_at_img, cv2.MORPH_CLOSE, close_kernel, iterations = 30)
    sure_bg = cv2.dilate(opening, dilate_kernel, iterations = 10)
    resized = cv2.resize(sure_bg, dsize=(1370, 530), interpolation=cv2.INTER_NEAREST)
    processed_x = (np.array(resized) / 255.0).reshape(-1, 530, 1370, 1)
    prediction = model.predict(processed_x, verbose = 0)[0][0] >= 1.0
    pet_pred.append(int(prediction))
    object_images.pop(0)

def database_update():
    global cursor, db
    global ids, names, pet_pred, empty_pred
    
    if pet_pred[0] == 1 and empty_pred[0] == 1:
        credit = 1
        arduino_message('spining')
    else:
        credit = 0
        arduino_message('spin&droping')
        # timing on the arduino must be modified (such that it only opens after spining) 
        
    cursor.execute("SELECT RFID_tag_no, Name FROM predefi WHERE RFID_tag_no="+str(ids[0]))
    result = cursor.fetchone() 
    if cursor.rowcount >= 1:
        cursor.execute("INSERT INTO card_tap (RFID_tag_no, PET_bottle, Empty, Credit) VALUES (%s, %s, %s, %s)", (result[0], pet_pred[0], empty_pred[0], credit))
        if credit == 1:
            cursor.execute("UPDATE predefi SET Points = Points + (%s) WHERE Name = (%s)", (credit, names[0]))
        db.commit()

    ids.pop(0)
    names.pop(0)
    pet_pred.pop(0)
    empty_pred.pop(0)


if __name__ == '__main__':
	weigh_taring()
	arduino_message('ready')
	
	try:
		while True:
			
			user_setup()
			
			chambers.pop(0)
			if (len(chambers) != 8):
				chambers.append(0)
				
			print(chambers)
			
			st_all = time.time()
			
			if chambers[2:7].count(1) != 0:
				if chambers[6] == 1:
					picamera_photo()
					print("PHOTO")
				if chambers[5] == 1:
					weighing_prediction()
					print("WEIGH")
				if chambers[4] == 1:
					pet_prediction()
					print("PET")
				if chambers[2] == 1:
					database_update()
					print("DATA")
				else:
					arduino_message('spining')
			else:
				arduino_message('spining')
				
			ed_all = time.time()
			time_spent = ed_all - st_all
			
			if time_spent < 2.0:
				time.sleep(2.0 - time_spent)
			
			lcd.clear()
			print('SINGLE CYCLE TIME: ' + str(ed_all - st_all))
			
			if multi_in:
				arduino_message('welcoming')
			else:
				arduino_message('ready')
	finally:
		GPIO.cleanup()
