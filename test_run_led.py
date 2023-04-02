#include all neccessary packages to get LEDs to work with Raspberry Pi
import time
import board
import neopixel

#Initialise a strips variable, provide the GPIO Data Pin
#utilised and the amount of LED Nodes on strip and brightness (0 to 1 value)
pixels1 = neopixel.NeoPixel(board.D18, 40, brightness=1)

#Focusing on a particular strip, use the command Fill to make it all a single colour
#based on decimal code R, G, B. Number can be anything from 255 - 0. Use a RGB Colour
#Code Chart Website to quickly identify a desired fill colour.
pixels1.fill((0, 0, 255))

#function simulation

while True:
    print('Idle state')
    pixels1.fill((0, 0, 255)) #blue in idle state
    
    print("Please tap card")
    input()
    pixels1.fill((0, 255, 0)) #bgreen in bottle insertion state
    time.sleep(3)
    print("Bottle inserted")
    time.sleep(3)
    
    print("Please press done button")
    input()
    print("Done button pressed")
    pixels1.fill((255, 0, 0)) #red in DO NOT INSERT state
    print("Is bottle PET and empty?")
    input()
    time.sleep(7)
    print("Bottle disposed")
    time.sleep(2)
    