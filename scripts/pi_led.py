#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 2.60
@date: 08/05/2022
'''

#un-comment for actual deployment on Raspberry Pi
#import RPi.GPIO as GPIO

#'''
#dummy GPIO "simulator" class & object
#comment for actual deployment on Raspberry Pi
class GPIO_DUMMY:
    HIGH = '3.3V'
    LOW = '0V'
    BCM = 'BCM'
    OUT = 'OUT'
    
    def output(self, port_no, value):
        print(f'SIMULATOR: Port {port_no} set to {value}')
    def setup(self, port_no, port_type):
        print(f'SIMULATOR: Port mode {port_no} set to {port_type}')
    def setmode(self, general_mode):
        print(f'SIMULATOR: General mode set to {general_mode}')
    def setwarnings(self, flag):
        print(f'SIMULATOR: Warnings set to {flag}')

GPIO = GPIO_DUMMY()
#'''

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class led:
    def __init__(self, led_id, led_port_no):
        self._led_id = led_id
        self._led_port_no = led_port_no
        #actual LED state can be either HIGH or LOW on initialization
        self._led_state_on = None
        
        GPIO.setup(self._led_port_no, GPIO.OUT)
    
    def turn_on(self):
        #print(f'turning on {self.led_id} LED')
        if self._led_state_on is None or not self._led_state_on:
            GPIO.output(self._led_port_no, GPIO.HIGH)
            self._led_state_on = True
    
    def turn_off(self):
        #print(f'turning off {self.led_id} LED')
        if self._led_state_on is None or self._led_state_on:
            GPIO.output(self._led_port_no, GPIO.LOW)
            self._led_state_on = False
            
    def is_on(self):
        return self._led_state_on
