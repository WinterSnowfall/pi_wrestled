#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 1.00
@date: 23/02/2020
'''

import threading
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from configparser import ConfigParser
from os import path
from time import sleep
from pi_led import led
from flask import Flask
from flask import request
from flask import Response

##global parameters init
configParser = ConfigParser()

##conf file block
conf_file_full_path = path.join('..', 'conf', 'led_array.conf')

##logging configuration block
log_file_full_path = path.join('..', 'logs', 'pi_wrestled_service.log')
logger_format = '%(asctime)s %(levelname)s >>> %(message)s'
logger_file_handler = RotatingFileHandler(log_file_full_path, maxBytes=0, backupCount=0, encoding='utf-8')
logger_file_formatter = logging.Formatter(logger_format)
logger_file_handler.setFormatter(logger_file_formatter)
logging.basicConfig(format=logger_format, level=logging.INFO) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger(__name__)
logger.addHandler(logger_file_handler)

io_lock = threading.Lock()

#reading from config file
configParser.read(conf_file_full_path)

KNIGHT_RIDER_INTERVAL = float(configParser['GENERAL']['knight_rider_interval'])
IDLE_WATCHDOG_INTERVAL = int(configParser['GENERAL']['idle_watchdog_interval'])
server_interface = configParser['GENERAL']['server_interface']
server_port = int(configParser['GENERAL']['server_port'])

#find out the host's main IP
logger.debug('Detecting host IP address...')
host_ip = subprocess.Popen(f"ip addr show {server_interface} | grep global | awk '{{print $2}}' | sed 's/\/.*//g'", 
                           shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8').strip()
logger.debug(f'Host address is: {host_ip}')

led_array = []
#special non-functional soft LED
led_array.append(led('knight_rider', 0))  #LED0

#parsing generic parameters
current_led_no = 1
#port numbers need to be specified as per the Raspberry Pi pinout layout: https://pinout.xyz
try:
    while True:
        current_led_name = configParser[f'LED{current_led_no}']['name']
        current_led_port = int(configParser[f'LED{current_led_no}']['port'])
        led_array.append(led(current_led_name, current_led_port))
        current_led_no += 1
except KeyError:
    logger.info(f'LED info parsing complete. Read {current_led_no - 1} entries.')

thread_array = [None for i in range(len(led_array))]
    
try:
    led_control = Flask(__name__)
    received = False
    knight_rider = False
    
    def led_control_server(var_host, var_port):
        led_control.run(host=var_host, port=var_port)
        
    def knight_rider_mode():
        global knight_rider
        
        with io_lock:
            logger.info('KR >>> Starting the show...')
        
        while True:
            #ascending
            for led_number in range(1, len(led_array)):
                with io_lock:
                    logger.debug(f'KR >>> LED number: {led_number}')
                
                if not knight_rider:
                    break
                else:
                    led_array[led_number].turn_on()
                    sleep(KNIGHT_RIDER_INTERVAL)
                    if led_number != len(led_array) - 1:
                        led_array[led_number].turn_off()
                    
            with io_lock:                        
                logger.debug('KR >>> Done ascending.')
                    
            #descending
            for led_number in range(len(led_array) - 1, 1, -1):
                with io_lock:
                    logger.debug(f'KR >>> LED number: {led_number}')
                
                if not knight_rider:
                    break
                else:
                    led_array[led_number].turn_on()
                    sleep(KNIGHT_RIDER_INTERVAL)
                    if led_number != 0:
                        led_array[led_number].turn_off()

            with io_lock:                        
                logger.debug('KR >>> Done descending.')
            
            if not knight_rider:
                break
        
        with io_lock:
            logger.info('KR >>> Show\'s over.')

    @led_control.route('/pi_led', methods=['POST'])
    def post():
        global received, knight_rider
        
        with io_lock:
            logger.info('Processing request...')
            logger.debug(request.is_json)
            
        content_array = request.get_json()
        
        with io_lock:
            logger.debug(f'Received message: {content_array}')
            logger.info('-------------------------')
            
        for content in content_array:
            try:
                with io_lock:
                    logger.debug('Parsing JSON request element...')
                
                led_number = content['led_no']
                led_state = content['state']
                led_blink = content['blink']
                
                with io_lock:
                    logger.info(f'LED number: {led_number}')
                    logger.info(f'LED state: {led_state}')
                    logger.info(f'LED blink interval: {led_blink}')
                    logger.info('-------------------------')
                    
                #regular LED control logic
                if led_number != 0:
                    if knight_rider:
                        knight_rider = False
                        sleep(KNIGHT_RIDER_INTERVAL)
                    
                    if led_state == 1 and led_blink == 0:
                        led_array[led_number].turn_on()
                        with io_lock:
                            logger.debug('LED turned on.')
                        
                    elif led_state == 0:
                        led_array[led_number].turn_off()
                        with io_lock:
                            logger.debug('LED turned off.')
                        
                    elif led_state == 1 and led_blink != 0:
                        try:
                            if thread_array[led_number].isAlive():
                                led_array[led_number].turn_off()
                                thread_array[led_number].join()
                        except AttributeError:
                            pass
                        
                        thread_array[led_number] = threading.Thread(target = led_array[led_number].blink, args = (led_blink, ))
                        thread_array[led_number].setDaemon(True)
                        thread_array[led_number].start()
                        
                        with io_lock:
                            logger.debug('LED is bliking.')
                    else:
                        raise Exception()
                        
                #Knight Rider mode
                else:
                    if knight_rider and led_state == 1:
                        with io_lock:
                            logger.warning('Knight Rider mode is already active!')
                    
                    elif not knight_rider and led_state == 1 :
                        with io_lock:
                            logger.info('Turning on Knight Rider mode!')
                 
                        knight_rider = True
                        
                        [led_array[i].turn_off() for i in range(1, len(led_array))]
                        
                        thread_array[0] = threading.Thread(target = knight_rider_mode)
                        thread_array[0].setDaemon(True)
                        thread_array[0].start()
                    else:
                        with io_lock:
                            logger.info('Turning off Knight Rider mode.')
                        
                        knight_rider = False
                        sleep(KNIGHT_RIDER_INTERVAL)
                        
            except:
                with io_lock:
                    logger.error('Invalid operation!')
                return Response('Invalid operation!', status=403, mimetype='text/html')
        
        received = True
        with io_lock:
            logger.info('Request processing completed.')
        
        return 'Operation completed!'

    #reset all LEDs
    logger.debug('Resetting all LEDs...')
    [led_array[i].turn_off() for i in range(1, len(led_array))]

    logger.info('Running REST endpoint server...')
    server_thread = threading.Thread(target=led_control_server, args=(host_ip, server_port))
    server_thread.setDaemon(True)
    server_thread.start()
    
    #need to io_lock from now on
    with io_lock:
        logger.info('Entering Knight Rider mode...')
    knight_rider = True
    thread_array[0] = threading.Thread(target = knight_rider_mode)
    thread_array[0].setDaemon(True)
    thread_array[0].start()
    
    with io_lock:
        #idle watchdog
        logger.info('Idle watchdog activated...')
    while True:
        #sleep for an interval
        sleep(IDLE_WATCHDOG_INTERVAL)
        with io_lock:
            logger.info('Idle watchdog wakeup...')
            if (not received):
                logger.warning('Idle watchdog has detected a timeout!')
                raise Exception()
            else:
                logger.info('Idle watchdog reset...')
                received = False
            
except:
    logger.debug('Turning off LEDs...')
    [led_array[i].turn_off() for i in range(1, len(led_array))]
    logger.debug('LEDs have been turned off.')
    #uncomment for debugging purposes only
    #raise

logger.info('REST endpoint server terminated.')
