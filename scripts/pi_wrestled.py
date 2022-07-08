#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 2.70
@date: 08/08/2022
'''

import threading
import signal
import logging
from configparser import ConfigParser
from os import path
from time import sleep
from pi_led import led
from flask import Flask
from flask import request
from flask import Response
#uncomment for debugging purposes only
#import traceback

##global parameters init
configParser = ConfigParser()

##conf file block
conf_file_full_path = path.join('..', 'conf', 'led_array.conf')

##logging configuration block
log_file_full_path = path.join('..', 'logs', 'pi_wrestled.log')
logger_file_handler = logging.FileHandler(log_file_full_path, mode='w', encoding='utf-8')
logger_format = '%(asctime)s %(levelname)s >>> %(message)s'
logger_file_handler.setFormatter(logging.Formatter(logger_format))
#logging level for other modules
logging.basicConfig(format=logger_format, level=logging.ERROR) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger(__name__)
#logging level for current logger
logger.setLevel(logging.INFO) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.addHandler(logger_file_handler)

#reading from config file
configParser.read(conf_file_full_path)
general_section = configParser['GENERAL']

KNIGHT_RIDER_INTERVAL = general_section.getfloat('knight_rider_interval')
### non-zero values will allow you to use a subset of the LED array for Knight Rider mode ###
KNIGHT_RIDER_START_LED = general_section.getint('knight_rider_start_led')
KNIGHT_RIDER_STOP_LED = general_section.getint('knight_rider_stop_led')
#############################################################################################
IDLE_WATCHDOG_INTERVAL = general_section.getint('idle_watchdog_interval')
INIT_BLINK_INTERVAL = general_section.getfloat('init_blink_interval')
server_port = general_section.getint('server_port')

led_array = []
#soft LED used for various effects
led_array.append(led('knight_rider', 0))

#parsing generic parameters
current_led_no = 0
#port numbers need to be specified as per the Raspberry Pi pinout layout: https://pinout.xyz
try:
    while True:
        current_led_no += 1
        current_led_section = configParser[f'LED{current_led_no}']
        current_led_name = current_led_section.get('name')
        current_led_port = current_led_section.getint('port')
        led_array.append(led(current_led_name, current_led_port))
except KeyError:
    logger.info(f'LED info parsing complete. Read {current_led_no - 1} entries.')

led_array_size = len(led_array)

#set default values for knight rider mode if no start/stop LEDs are specified
#(will use the entire LED array, as defined in the config file)
if KNIGHT_RIDER_START_LED == 0:
    KNIGHT_RIDER_START_LED = 1

if KNIGHT_RIDER_STOP_LED == 0:
    KNIGHT_RIDER_STOP_LED = led_array_size - 1

thread_array = [None for i in range(led_array_size)]
blink_array = [False for i in range(led_array_size)]

led_control = Flask(__name__)
received = False
knight_rider = False
init_mode = True

def sigterm_handler(signum, frame):
    logger.info('Stopping wrestled due to SIGTERM...')
    
    logger.debug('Turning off LEDs...')
    for i in range(1, led_array_size):
        led_array[i].turn_off()
    logger.debug('LEDs have been turned off.')
    
    raise SystemExit(0)

def led_control_server(var_host, var_port):
    led_control.run(host=var_host, port=var_port)
        
def led_init_mode():
    logger.debug('IM >>> Entering LED init test mode...')
        
    odd_on_state = True
        
    while init_mode:
        for led_number in range(1, led_array_size):
            if led_number % 2 == 1:
                if odd_on_state:
                    led_array[led_number].turn_on()
                else:
                    led_array[led_number].turn_off()
            else:
                if odd_on_state:
                    led_array[led_number].turn_off()
                else:
                    led_array[led_number].turn_on()
        
        odd_on_state = not odd_on_state
        
        sleep(INIT_BLINK_INTERVAL)
        
    logger.debug('Resetting all LEDs...')
    for i in range(1, led_array_size):
        led_array[i].turn_off()
        
    logger.debug('IM >>> Exiting init LED test mode...')
    
def led_blink_mode(led_number, led_blink):
    global blink_array
    
    logger.debug(f'BM >>> LED {led_number} blinking for {led_blink}...')
    
    blink_array[led_number] = True
    
    if led_array[led_number].is_on():
        led_array[led_number].turn_off()
    
    while True:
        #perform blink state checks before changing state for off->on transitions,
        #in order to ensure that all LEDs stop blinking while in an off state
        if not blink_array[led_number]:
            logger.debug(f'BM >>> LED {led_number} stopped blinking.')
            return
        led_array[led_number].turn_on()
        
        sleep(led_blink)
        
        led_array[led_number].turn_off()
        if not blink_array[led_number]:
            logger.debug(f'BM >>> LED {led_number} stopped blinking.')
            return
        
        sleep(led_blink)
    
def knight_rider_mode():
    logger.debug('KR >>> Starting the show...')
    
    while True:
        #ascending
        for led_number in range(KNIGHT_RIDER_START_LED, KNIGHT_RIDER_STOP_LED + 1):
            logger.debug(f'KR >>> LED number: {led_number}')
            
            if not knight_rider:
                break
            else:
                led_array[led_number].turn_on()
                sleep(KNIGHT_RIDER_INTERVAL)
                #cater for cases in which Knight Rider mode is
                #turned off while the end led is on
                if led_number != led_array_size - 1 or not knight_rider:
                    led_array[led_number].turn_off()
                
        logger.debug('KR >>> Done ascending.')
                
        #descending
        for led_number in range(KNIGHT_RIDER_STOP_LED, 0, -1):
            logger.debug(f'KR >>> LED number: {led_number}')
            
            if not knight_rider:
                break
            else:
                led_array[led_number].turn_on()
                sleep(KNIGHT_RIDER_INTERVAL)
                #cater for cases in which Knight Rider mode is
                #turned off while the start led is on
                if led_number != 1 or not knight_rider:
                    led_array[led_number].turn_off()

        logger.debug('KR >>> Done descending.')
        
        if not knight_rider:
            break
    
    logger.debug('KR >>> Show\'s over.')

@led_control.route('/pi_led', methods=['POST'])
def post():
    global thread_array, blink_array, received, knight_rider, init_mode
    
    if init_mode:
        init_mode = False
        thread_array[0].join()
    
    logger.info('Processing request...')
    
    logger.debug(f'REST payload JSON conformance: {request.is_json}')    
    content_array = request.get_json()
    
    logger.debug(f'Received message: {content_array}')
    logger.info('-----------------------------')
        
    for content in content_array:
        try:
            logger.debug('Parsing JSON request element...')
            
            led_number = content['led_no']
            led_state = content['state']
            led_blink = content['blink']
            
            logger.info(f'LED number: {led_number}')
            logger.info(f'LED state: {led_state}')
            logger.info(f'LED blink interval: {led_blink}')
            logger.info('-----------------------------')
                
            #regular LED control logic
            if led_number != 0:
                if knight_rider:
                    if led_number >= KNIGHT_RIDER_START_LED and led_number <= KNIGHT_RIDER_STOP_LED:
                        logger.info('Turning off Knight Rider mode...')
                        
                        knight_rider = False
                        thread_array[0].join()
                    else:
                        logger.debug('Current LED is outside of the Knight Rider LED range.')
                
                #wait for LED blink to finalize if active
                try:
                    if blink_array[led_number]:
                        logger.debug('Stopping active LED blink thread...')
                        
                        blink_array[led_number] = False
                        thread_array[led_number].join()
                        
                        logger.debug('LED blink thread stopped.')
                except AttributeError:
                    pass
                
                if led_state == 0:
                    led_array[led_number].turn_off()
                    logger.debug('LED turned off.')
                
                elif led_state == 1 and led_blink == 0:
                    led_array[led_number].turn_on()
                    logger.debug('LED turned on.')
                    
                elif led_state == 1 and led_blink != 0:
                    thread_array[led_number] = threading.Thread(target=led_blink_mode, 
                                                                args=(led_number, led_blink), daemon=True)
                    thread_array[led_number].start()
                    logger.debug('LED is bliking.')
                
                else:
                    raise Exception('Invalid LED state.')
                    
            #Knight Rider mode
            else:
                if knight_rider and led_state == 1:
                    logger.warning('Knight Rider mode is already active.')
                    
                elif not knight_rider and led_state == 0:
                    logger.info('Turning off Knight Rider mode...')
                    
                    knight_rider = False
                    thread_array[0].join()
                
                elif not knight_rider and led_state == 1:
                    logger.info('Turning on Knight Rider mode...')
             
                    knight_rider = True
                    
                    for i in range(KNIGHT_RIDER_START_LED, KNIGHT_RIDER_STOP_LED + 1):
                        if blink_array[i]:
                            blink_array[i] = False
                            thread_array[i].join()
                        else:
                            led_array[i].turn_off()
                    
                    thread_array[0] = threading.Thread(target=knight_rider_mode, daemon=True)
                    thread_array[0].start()
                
                else:
                    raise Exception('Invalid Knight Rider state.')
                
        except:
            #uncomment for debugging purposes only
            #logger.error(traceback.format_exc())
            
            logger.error('Invalid operation.')
            return Response('Invalid operation.', status=403, mimetype='text/html')
    
    logger.info('Request processing completed.')
    received = True
    
    return 'Operation completed.'

##main thread start

try:
    logger.info('Running REST endpoint server...')
    
    #use '0.0.0.0' to listen on all network interfaces, regardless of link status during startup
    server_thread = threading.Thread(target=led_control_server, args=('0.0.0.0', server_port), daemon=True)
    server_thread.start()
    
    #catch SIGTERM and exit gracefully
    signal.signal(signal.SIGTERM, sigterm_handler)
    
    logger.info('Starting LED test mode...')
    thread_array[0] = threading.Thread(target=led_init_mode, daemon=True)
    thread_array[0].start()
    
    logger.info('Activating idle watchdog...')
    
    while True:
        sleep(IDLE_WATCHDOG_INTERVAL)
        
        logger.debug('Idle watchdog wakeup...')
        
        if not received:
            logger.warning('Idle watchdog has detected a timeout.')
            raise Exception()
        else:
            logger.debug('Idle watchdog reset...')
            received = False
          
except:
    logger.debug('Turning off LEDs...')
    for i in range(1, led_array_size):
        led_array[i].turn_off()
    logger.debug('LEDs have been turned off.')
    #uncomment for debugging purposes only
    #logger.error(traceback.format_exc())

logger.info('REST endpoint server terminated.')

##main thread end
