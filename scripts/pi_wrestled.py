#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 2.80
@date: 10/12/2022
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

##conf file block
conf_file_full_path = path.join('..', 'conf', 'led_array.conf')

##logging configuration block
log_file_full_path = path.join('..', 'logs', 'pi_wrestled.log')
logger_file_handler = logging.FileHandler(log_file_full_path, encoding='utf-8')
logger_format = '%(asctime)s %(levelname)s >>> %(message)s'
logger_file_handler.setFormatter(logging.Formatter(logger_format))
#logging level for other modules
logging.basicConfig(format=logger_format, level=logging.ERROR) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger(__name__)
#logging level defaults to INFO, but can be later modified through config file values
logger.setLevel(logging.INFO)
logger.addHandler(logger_file_handler)

HTTP_BAD_REQUEST = 400
led_control = Flask(__name__)

def sigterm_handler(signum, frame):
    logger.debug('Stopping wrestled due to SIGTERM...')
    
    raise SystemExit(0)

def sigint_handler(signum, frame):
    logger.debug('Stopping wrestled due to SIGINT...')
    
    raise SystemExit(0)

def led_control_server(var_host, var_port):
    led_control.run(host=var_host, port=var_port)

def led_init_mode():
    logger.debug('IM >>> Entering LED init test mode...')
    
    odd_on_state = True
    
    while not init_event_stop.is_set():
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

def knight_rider_mode():
    logger.debug('KR >>> Starting the show...')
    
    while not knight_rider_stop.is_set():
        #ascending
        for led_number in range(KNIGHT_RIDER_START_LED, KNIGHT_RIDER_STOP_LED + 1):
            logger.debug(f'KR >>> LED number: {led_number}')
            
            if knight_rider_stop.is_set():
                break
            else:
                led_array[led_number].turn_on()
                sleep(KNIGHT_RIDER_INTERVAL)
                #cater for cases in which Knight Rider mode is
                #turned off while the end led is on
                if led_number != led_array_size - 1 or knight_rider_stop.is_set():
                    led_array[led_number].turn_off()
        
        logger.debug('KR >>> Done ascending.')
        
        #descending
        for led_number in range(KNIGHT_RIDER_STOP_LED, 0, -1):
            logger.debug(f'KR >>> LED number: {led_number}')
            
            if knight_rider_stop.is_set():
                break
            else:
                led_array[led_number].turn_on()
                sleep(KNIGHT_RIDER_INTERVAL)
                #cater for cases in which Knight Rider mode is
                #turned off while the start led is on
                if led_number != 1 or knight_rider_stop.is_set():
                    led_array[led_number].turn_off()

        logger.debug('KR >>> Done descending.')
    
    logger.debug('KR >>> Show\'s over.')

@led_control.route('/pi_led', methods=['POST'])
def post():
    if not init_event_stop.is_set():
        init_event_stop.set()
        init_mode_thread.join()
    
    #the Knight Rider thread is stored as part of soft LED 0
    knight_rider_thread = led_array[0].get_thread()
    
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
                if not knight_rider_stop.is_set():
                    if led_number >= KNIGHT_RIDER_START_LED and led_number <= KNIGHT_RIDER_STOP_LED:
                        logger.info('Turning off Knight Rider mode...')
                        
                        knight_rider_stop.set()
                        knight_rider_thread.join()
                    else:
                        logger.debug('Current LED is outside of the Knight Rider LED range.')
                
                #wait for LED blink to finalize if active
                if led_array[led_number].is_blinking():
                    logger.debug('Stopping active LED blink thread...')
                    
                    led_array[led_number].turn_off()
                    led_array[led_number].join()
                    
                    logger.debug('LED blink thread stopped.')
                
                if led_state == 0:
                    led_array[led_number].turn_off()
                    logger.debug('LED turned off.')
                
                elif led_state == 1 and led_blink == 0:
                    led_array[led_number].turn_on()
                    logger.debug('LED turned on.')
                
                elif led_state == 1 and led_blink != 0:
                    logger.debug(f'LED {led_number} blinking for {led_blink}...')
                    led_array[led_number].blink(led_blink)
                    logger.debug('LED is bliking.')
                
                else:
                    raise Exception('Invalid LED state.')
            
            #Soft LED 0 - Knight Rider mode
            else:
                if not knight_rider_stop.is_set() and led_state == 1:
                    logger.warning('Knight Rider mode is already active.')
                
                elif not knight_rider_stop.is_set() and led_state == 0:
                    logger.info('Turning off Knight Rider mode...')
                    
                    knight_rider_stop.set()
                    knight_rider_thread.join()
                
                elif knight_rider_stop.is_set() and led_state == 1:
                    logger.info('Turning on Knight Rider mode...')
                    
                    knight_rider_stop.clear()
                    
                    for i in range(KNIGHT_RIDER_START_LED, KNIGHT_RIDER_STOP_LED + 1):
                        if led_array[i].is_blinking():
                            logger.debug(f'LED {i} is blinking. Turning it off...')
                            led_array[i].turn_off()
                            led_array[i].join()
                        else:
                            logger.debug(f'Turning off LED {i}...')
                            led_array[i].turn_off()
                    
                    knight_rider_thread = threading.Thread(target=knight_rider_mode, daemon=True)
                    knight_rider_thread.start()
                    led_array[0].set_thread(knight_rider_thread)
                    
                    logger.debug('Knight Rider mode initiated.')
                
                else:
                    raise Exception('Invalid Knight Rider state.')
        
        except:
            #uncomment for debugging purposes only
            #logger.error(traceback.format_exc())
            logger.error('Invalid operation.')
            
            return Response('Invalid operation.', status=HTTP_BAD_REQUEST, mimetype='text/html')
    
    logger.info('Request processing completed.')
    
    timed_out.clear()
    
    return 'Operation completed.'

if __name__ == "__main__":
    #catch SIGTERM and exit gracefully
    signal.signal(signal.SIGTERM, sigterm_handler)
    #catch SIGINT and exit gracefully
    signal.signal(signal.SIGINT, sigint_handler)
    
    configParser = ConfigParser()
    
    try:
        configParser.read(conf_file_full_path)
        
        general_section = configParser['GENERAL']
        LOGGING_LEVEL = general_section.get('logging_level').upper()
        
        #DEBUG, INFO, WARNING, ERROR, CRITICAL
        #remains set to INFO if none of the other valid log levels are specified
        if LOGGING_LEVEL == 'INFO':
            pass
        elif LOGGING_LEVEL == 'DEBUG':
            logger.setLevel(logging.DEBUG)
        elif LOGGING_LEVEL == 'WARNING':
            logger.setLevel(logging.WARNING)
        elif LOGGING_LEVEL == 'ERROR':
            logger.setLevel(logging.ERROR)
        elif LOGGING_LEVEL == 'CRITICAL':
            logger.setLevel(logging.CRITICAL)
        
        KNIGHT_RIDER_INTERVAL = general_section.getfloat('knight_rider_interval')
        #non-zero values for start and stop LEDs will allow you to 
        #use a subset of the LED array for Knight Rider mode
        KNIGHT_RIDER_START_LED = general_section.getint('knight_rider_start_led')
        KNIGHT_RIDER_STOP_LED = general_section.getint('knight_rider_stop_led')
        IDLE_WATCHDOG = general_section.getboolean('idle_watchdog')
        IDLE_WATCHDOG_INTERVAL = general_section.getint('idle_watchdog_interval')
        INIT_BLINK_INTERVAL = general_section.getfloat('init_blink_interval')
        server_port = general_section.getint('server_port')
    
    except:
        logger.critical('Could not parse configuration file. Please make sure the appropriate structure is in place!')
        raise SystemExit(1)
    
    logger.info('wrestled is starting...')
    
    #soft LED 0 is used for Knight Rider mode
    led_array = [led('knight_rider', 0)]
    current_led_no = 0
    
    try:
        while True:
            current_led_no += 1
            current_led_section = configParser[f'LED{current_led_no}']
            current_led_name = current_led_section.get('name')
            #port numbers need to be specified as per the Raspberry Pi pinout layout: https://pinout.xyz
            current_led_port = current_led_section.getint('port')
            led_array.append(led(current_led_name, current_led_port))
    
    except KeyError:
        logger.info(f'LED info parsing complete. Read {current_led_no - 1} entries.')
    
    except:
        logger.critical('Could not parse LED entries. Please make sure the appropriate structure is in place!')
        raise SystemExit(2)
    
    led_array_size = len(led_array)
    
    #set default values for knight rider mode if no start/stop LEDs are specified
    #(will use the entire LED array, as defined in the config file)
    if KNIGHT_RIDER_START_LED == 0:
        KNIGHT_RIDER_START_LED = 1
    if KNIGHT_RIDER_STOP_LED == 0:
        KNIGHT_RIDER_STOP_LED = led_array_size - 1
    
    timed_out = threading.Event()
    timed_out.clear()
    init_event_stop = threading.Event()
    init_event_stop.clear()
    knight_rider_stop = threading.Event()
    knight_rider_stop.set()
    
    try:
        logger.info('Running REST endpoint server...')
        
        #use '0.0.0.0' to listen on all network interfaces, regardless of link status during startup
        server_thread = threading.Thread(target=led_control_server, args=('0.0.0.0', server_port), daemon=True)
        server_thread.start()
        
        logger.info('Starting LED test mode...')
        init_mode_thread = threading.Thread(target=led_init_mode, daemon=True)
        init_mode_thread.start()
        
        logger.info('Activating idle watchdog...')
        
        if IDLE_WATCHDOG:
            while not timed_out.is_set():
                timed_out.set()
                sleep(IDLE_WATCHDOG_INTERVAL)
                logger.debug('Idle watchdog wakeup...')
                
            logger.warning('Idle watchdog has detected a timeout.')
        else:
            timed_out.wait()
    
    except SystemExit:
        init_event_stop.set()
        knight_rider_stop.set()
        
        logger.info('Stopping wrestled...')
    
    finally:
        init_mode_thread.join()
        
        logger.debug('Turning off LEDs...')
        for i in range(1, led_array_size):
            led_array[i].turn_off()
        logger.debug('LEDs have been turned off.')
        
        #join all threads, including soft LED 0
        for i in range(led_array_size):
            led_array.join()
        
    logger.info('REST endpoint server terminated.')
