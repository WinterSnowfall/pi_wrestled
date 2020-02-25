#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 1.00
@date: 23/02/2020
'''

#un-comment for actual deployment on Raspberry Pi
#import RPi.GPIO as GPIO
from time import sleep

#'''
#dummy GPIO "simulator" class & object
#comment for actual deployment on Raspberry Pi
class GPIO_DUMMY:
    def output(self, port_no, value):
        print(f'SIMULATOR: Port {port_no} set to {value}')
    def setup(self, port_no, port_type):
        print(f'SIMULATOR: Port mode {port_no} set to {port_type}')
    def setmode(self, general_mode):
        print(f'SIMULATOR: General mode set to {general_mode}')
    def setwarnings(self, flag):
        print(f'SIMULATOR: Warnings set to {flag}')
        
    HIGH = '3.3V'
    LOW = '0V'
    BCM = 'BCM'
    OUT = 'OUT'
    
GPIO = GPIO_DUMMY()
#'''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class led:
    def __init__(self, led_id, led_port_no):
        self.led_id = led_id
        self.led_port_no = led_port_no
        self.led_history = False
        self.led_state = 0
        self.led_blink = 0
        self.led_blink_interval = 0
        
        GPIO.setup(led_port_no, GPIO.OUT)
    
    def turn_on(self):
        self.led_blink = 0
        self.led_blink_interval = 0
        #print(f'turning on {self.led_id} LED')
        if self.led_state == 0:
            self.led_state = 1
            GPIO.output(self.led_port_no,GPIO.HIGH)
            self.led_history = True
    
    def turn_off(self):
        self.led_blink = 0
        self.led_blink_interval = 0
        #print(f'turning off {self.led_id} LED')
        if self.led_state == 1 or not self.led_history:
            self.led_state = 0
            GPIO.output(self.led_port_no,GPIO.LOW)
            self.led_history = True
    
    def blink(self, blink_interval):
        self.led_blink = 1
        #led_state should be set as well, since a blink cycle
        #will typically end with a HIGH power state
        self.led_state = 1
        #print(f'blinking {self.led_id} LED')
        if self.led_blink_interval != blink_interval:
            self.led_blink_interval = blink_interval
            while self.led_blink == 1:
                GPIO.output(self.led_port_no,GPIO.LOW)
                sleep(blink_interval)
                GPIO.output(self.led_port_no,GPIO.HIGH)
                sleep(blink_interval)
            #check if a different thread has not turned off the LED,
            #and, if so, leave it in a LOW power state
            if self.led_state == 0:
                GPIO.output(self.led_port_no,GPIO.LOW)
            self.led_history = True
