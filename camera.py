# """
from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.rotation = 90
# camera.resolution = (1920, 1080)

camera.start_preview()
sleep(10)
camera.capture('/home/ssc402/Desktop/test.jpg')
camera.stop_preview()

"""
import func_timeout

def enter_btn():
	enter = input("THROW")

def press_btn():
	try:
		func_timeout.func_timeout(2, enter_btn, args=[])
		print("PRESSED")
	except func_timeout.FunctionTimedOut:
		print("END")

press_btn()

"""
