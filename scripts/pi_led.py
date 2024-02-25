#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 3.00
@date: 21/02/2024
'''

import threading
from time import sleep
######################################################
# un-comment for actual deployment on a Raspberry Pi #
######################################################
#'''
from gpiozero import LED as LED_ZERO
import RPi.GPIO as GPIO
#'''
######################################################

######################################################
# comment for actual deployment on a Raspberry Pi    #
######################################################
'''
# simple logging RPi.GPIO simulator
class GPIO_DUMMY:
    HIGH = '3.3V'
    LOW = '0V'
    BCM = 'BCM'
    OUT = 'OUT'

    @staticmethod
    def output(port_no, value):
        print(f'SIMULATOR: Port {port_no} set to {value}')

    @staticmethod
    def setup(port_no, port_type):
        print(f'SIMULATOR: Port mode {port_no} set to {port_type}')

    @staticmethod
    def setmode(general_mode):
        print(f'SIMULATOR: General mode set to {general_mode}')

    @staticmethod
    def setwarnings(flag):
        print(f'SIMULATOR: Warnings set to {flag}')

GPIO = GPIO_DUMMY()

# simple logging gpiozero simulator
class LED_ZERO:

    def __init__(self, led_port_no):
        self.led_port_no = led_port_no

    def on(self):
        print(f'SIMULATOR: On state on port {self.led_port_no}')

    def off(self):
        print(f'SIMULATOR: Off state on port {self.led_port_no}')
'''
######################################################

################### BACKEND CONFIG ###################
PI_LED_BACKENDS = ('gpiozero', 'RPi.GPIO')
# 'gpiozero' is required for deployment on 
# a Raspberry Pi 5, and generally recommended,
# while 'RPi.GPIO' is included as a fallback
PI_LED_USED_BACKEND = 'gpiozero'
######################################################

if PI_LED_USED_BACKEND == PI_LED_BACKENDS[1]:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

class led:

    def __init__(self, led_id, led_port_no):
        self._led_id = led_id
        self._led_port_no = led_port_no
        self._led_state_on = False
        self._led_blink = False
        self._led_thread = None

        if PI_LED_USED_BACKEND == PI_LED_BACKENDS[0]:
            self._led = LED_ZERO(self._led_port_no)
        elif PI_LED_USED_BACKEND == PI_LED_BACKENDS[1]:
            GPIO.setup(self._led_port_no, GPIO.OUT)
            # set LED to LOW state on init
            GPIO.output(self._led_port_no, GPIO.LOW)

    def turn_on(self):
        #print(f'turning on {self.led_id} LED')
        if self._led_blink:
            self._led_blink = False

        if not self._led_state_on:
            if PI_LED_USED_BACKEND == PI_LED_BACKENDS[0]:
                self._led.on()
            elif PI_LED_USED_BACKEND == PI_LED_BACKENDS[1]:
                GPIO.output(self._led_port_no, GPIO.HIGH)
            self._led_state_on = True

    def turn_off(self):
        #print(f'turning off {self.led_id} LED')
        if self._led_blink:
            self._led_blink = False

        if self._led_state_on:
            if PI_LED_USED_BACKEND == PI_LED_BACKENDS[0]:
                self._led.off()
            elif PI_LED_USED_BACKEND == PI_LED_BACKENDS[1]:
                GPIO.output(self._led_port_no, GPIO.LOW)
            self._led_state_on = False

    def _blink(self, interval):
        #print(f'blinking {self.led_id} LED')

        while self._led_blink:
            if PI_LED_USED_BACKEND == PI_LED_BACKENDS[0]:
                self._led.on()
            elif PI_LED_USED_BACKEND == PI_LED_BACKENDS[1]:
                GPIO.output(self._led_port_no, GPIO.HIGH)
            self._led_state_on = True
            sleep(interval)

            # eagerly exit if no longer blinking
            if not self._led_blink:
                return

            if PI_LED_USED_BACKEND == PI_LED_BACKENDS[0]:
                self._led.off()
            elif PI_LED_USED_BACKEND == PI_LED_BACKENDS[1]:
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
                                            args=(interval,), daemon=True)
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
