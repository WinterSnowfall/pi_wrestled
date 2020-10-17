#!/bin/bash

nohup ./pi_wrestled.py 1>/dev/null 2>&1 &
sleep 2s
echo "Service started - now tailing logs. Press CTRL + C to exit."
tail -f ../logs/pi_wrestled_service.log
