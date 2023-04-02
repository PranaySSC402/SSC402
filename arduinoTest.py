import serial
import time

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.reset_input_buffer()
    
    while True:
        print("null")
        ser.write(b'0')
        time.sleep(1)
        
        print("spining")
        ser.write(b'1')
        time.sleep(1)
        
        print("spin&droping")
        ser.write(b'2')
        time.sleep(1)
        
        print("green light")
        ser.write(b'3')
        time.sleep(1)
        
        print("red light")
        ser.write(b'4')
        time.sleep(1)
        
        print("blue light")
        ser.write(b'5')
        time.sleep(1)
        
        print("image light")
        ser.write(b'6')
        time.sleep(1)
