# pi_wrestled
The next best thing after the invention of garlic bread. Well, yes, but actually no. It's actually my own version of this: https://projects.raspberrypi.org/en/projects/dancing-unicorn-rainbow minus the dancing unicorn, but adding individual LED control via REST calls. It's written in python3, using the RPi.GPIO interfaces to set LED states, which is pretty much the standard way to do it with a Raspberry Pi.

## What does/can it do?

It lets you define your own led arrays and link soft LEDs with hardware pins (you can connect as many LEDs as you want) and control them via REST calls. The server also includes a watchdog which will automatically stop the REST server (and power off all LEDs) if no commands are passed to it for a set amount of time.

## What do I need to do to get it running on my Raspberry Pi?

Asumming you're using the default Raspbian, I think everything's already there. You may need to manually install flask for python3, as follows:
```
sudo apt-get install python3-flask
```

## REST??? How does that work?

You'll need a REST client. Any will do, really.

As for the playload you need to pass, doing a POST on <host_ip>:<host_port>/pi_led with one or multiple led entries, as follows:


```
[{
"led_no": 1,
"state": 1,
"blink": 0
},
{
"led_no": 2,
"state": 0,
"blink": 0
},
{
"led_no": 3,
"state": 1,
"blink": 1
}]
```

"state" controls on/off LED states, "blink" interval, in seconds, for automatic switching between the two states.

There's also a special "0" soft LED which controls a "Knight Rider" or "KITT" effect for your LED array, as shown here: https://media.tenor.com/images/09bb20a1e40457b7897ee99a13b6a8a9/tenor.gif

This effect is automatically started with the pi_wrestled server and notifies you it is ready to receieve your REST calls. It also provides a way of validating that all your LEDs are working properly.

## How do you map the GPIO pins to LEDs?

It's all in led_array.conf (an actual live sample is provided based on my LED array setup). For pin numbers please see: https://pinout.xyz

## Can this break my Pi?

Not if you've set up your LEDs properly, using resistors, not shorting things etc. Make sure you've gotten familiar with the hardware part and how that needs to be set up properly before you worry about pi_wrestled.


