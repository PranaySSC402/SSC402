import os
import cv2
import time
import numpy as np
from PIL import Image
from tensorflow import keras
from picamera import PiCamera

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

img_array = []
img_directory = {1: 'datasets/pet-bottle', 0: 'datasets/non-pet'}

for key in img_directory.keys():
    for img_name in os.listdir(img_directory[key]):
        if 'jpg' in img_name:
            if "._" in img_name:
                img_name = img_name[2:]
            img_data = np.array(Image.open(os.path.join(img_directory[key], img_name)).convert("L"))
            img_array.append(img_data)

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
    if weight > 90:
        prediction = 0
    else:
        prediction = 1
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
        # scan id
        ids = input('Enter your id: ')
        arduino_message('spin')     # chamber 1 -> 2

        # take photo
        st = time.time()
        image_x = picamera_photo()
        ed = time.time()
        print('imaging time: ' + str(ed - st))
        arduino_message('spin')     # chamber 2 -> 3
        
        # measure weight
        st = time.time()
        weight_info = 80
        time.sleep(3)
        ed = time.time()
        print('weighing time: ' + str(ed - st))
        arduino_message('spin')     # chamber 3 -> 4

        image_x = img_array[int(ids)]

        # pet prediction
        st = time.time()
        pet_pred = pet_prediction(image_x)
        ed = time.time()
        print('pet prediction time: ' + str(ed - st))
        arduino_message('spin')     # chamber 4 -> 5

        # emptiness prediction
        st = time.time()
        empty_pred = empty_prediction(weight_info)
        ed = time.time()
        print('empty prediction time: ' + str(ed - st))
        arduino_message('spin')     # chamber 5 -> 6

        credit = 0
        if (not pet_pred) or (not empty_pred):   
            arduino_message('spin&drop')     # chamber 6 -> 7
        else:
            arduino_message('spin')          # chamber 6 -> 7
            credit = 1

        # store data on databse
        print("result: " + str(pet_pred) + " and " + str(empty_pred) + " for " + ids)
        arduino_message('spin')     # chamber 7 -> 8
        
        # send email
        arduino_message('spin')     # chamber 8 -> 1
    
finally:
    # GPIO.cleanup()
    pass
