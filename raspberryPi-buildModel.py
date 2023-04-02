import os
import cv2
import keras
import numpy as np
from PIL import Image
from keras.models import Sequential
from sklearn.model_selection import train_test_split
from keras.layers import Conv2D, MaxPooling2D, AveragePooling2D, Flatten, Dense

img_array = []
img_class = []
img_directory = {1: 'datasets/pet-bottle', 0: 'datasets/non-pet'}

for key in img_directory.keys():
    for img_name in os.listdir(img_directory[key]):
        if img_name[-5] in ['a', 'b', 'e', 'g', 'i', 'k']:
            if ('._' in img_name):
                img_name = img_name[2:]
            img_data = np.array(Image.open(os.path.join(img_directory[key], img_name)).convert("L"))
            img_array.append(img_data[275:805, 95:1465])
            img_class.append(key)
            img_array.append(np.flipud(img_array[-1]))
            img_class.append(key)

processed_img = []

pixel_diameter = 11
sigma_space = 75
sigma_color = 75

param_adaptiveMethod = cv2.ADAPTIVE_THRESH_MEAN_C
param_thresholdType = cv2.THRESH_BINARY_INV
param_blockSize = 21
param_C = 2

close_kernel = np.ones((2, 2), np.uint8)
dilate_kernel = np.ones((2, 2), np.uint8)

for img_data in img_array:
    img_blf = cv2.bilateralFilter(img_data, pixel_diameter, sigma_space, sigma_color)
    img_at = cv2.adaptiveThreshold(img_blf, img_blf.max(), param_adaptiveMethod, param_thresholdType, param_blockSize, param_C)
    img_close = cv2.morphologyEx(img_at, cv2.MORPH_CLOSE, close_kernel, iterations = 30)
    img_dilate = cv2.dilate(img_close, dilate_kernel, iterations = 10)
    processed_img.append(img_dilate)

image_x = (np.array(processed_img) / 255.0).reshape(-1, 530, 1370, 1)
x_train, x_test, y_train, y_test = train_test_split(image_x, np.array(img_class), test_size=0.33, shuffle=True)

model = Sequential([
    Conv2D(64, kernel_size=(9, 9), input_shape=(530, 1370, 1), activation='relu'),
    MaxPooling2D(pool_size=(3, 3)),
    Conv2D(64, (5, 5), activation='relu'),
    AveragePooling2D(pool_size=(3, 3)),
    Conv2D(64, (5, 5), activation='relu'),
    AveragePooling2D(pool_size=(3, 3)),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.summary()

print('Model Optimization Started')

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(x=x_train, y=y_train, batch_size=10, epochs=5)
model.save('trained_model')

print('Model Saved')

loaded_model = keras.models.load_model('trained_model')
score = loaded_model.evaluate(x=x_test, y=y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])
