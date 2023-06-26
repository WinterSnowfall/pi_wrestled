#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 2.92
@date: 26/06/2023
'''

import threading
from time import sleep
# un-comment for actual deployment on Raspberry Pi
#import RPi.GPIO as GPIO

#'''
# dummy GPIO "simulator" class & object
# comment for actual deployment on Raspberry Pi
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
        self._led_state_on = False
        self._led_blink = False
        self._led_thread = None
        
        GPIO.setup(self._led_port_no, GPIO.OUT)
        # set LED to LOW state on init
        GPIO.output(self._led_port_no, GPIO.LOW)
    
    def turn_on(self):
        #print(f'turning on {self.led_id} LED')
        if self._led_blink:
            self._led_blink = False
        
        if not self._led_state_on:
            GPIO.output(self._led_port_no, GPIO.HIGH)
            self._led_state_on = True
    
    def turn_off(self):
        #print(f'turning off {self.led_id} LED')
        if self._led_blink:
            self._led_blink = False
            
        if self._led_state_on:
            GPIO.output(self._led_port_no, GPIO.LOW)
            self._led_state_on = False
                
    def _blink(self, interval):
        #print(f'blinking {self.led_id} LED')
            
        while self._led_blink:
            GPIO.output(self._led_port_no, GPIO.HIGH)
            self._led_state_on = True
            sleep(interval)
            
            # eagerly exit if no longer blinking
            if not self._led_blink:
                return
            
            GPIO.output(self._led_port_no, GPIO.LOW)
            self._led_state_on = False
            sleep(interval)
            
    def blink(self, interval):
        # shouldn't happen in practice, but join if the blink thread is active
        if self._led_blink:
            self._led_blink = False
            self._led_thread.join()
            
        self._led_blink = True
        
        self._led_thread = threading.Thread(target=self._blink, 
                                            args=(interval, ), daemon=True)
        self._led_thread.start()
        
    def join(self):
        try:
            self._led_thread.join()
        except AttributeError:
            pass
        
    def get_thread(self):
        return self._led_thread
    
    def set_thread(self, thread):
        self._led_thread = thread
            
    def is_blinking(self):
        return self._led_blink
