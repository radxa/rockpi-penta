#!/usr/bin/env python3
import sys
import time
import fan
import misc
import multiprocessing as mp

""" Conditionally import the oled functions and flag if
    the top_board seems to exist.
    Log any exception generated.
"""
try:
    import oled
    top_board = 1
except Exception as ex:
    top_board = 0
    print (ex)


q = mp.Queue()              # communication on watch_key/receive_key
display_queue = mp.Queue()  # communication in the display processor

refresh_theshold = 0.1    # we will not refresh if period is less than this (seconds)

action = {
    'none': lambda: 'nothing',
    'slider': lambda: display_queue.put(True),
    'switch': lambda: misc.fan_switch(),
    'reboot': lambda: misc.check_call('reboot'),
    'poweroff': lambda: misc.check_call('poweroff --halt'),
}

"""
   Receive a user input from the queue as a 'key' value
   to get the processing function and then run the action
   for it.
"""
def receive_key(q):
    while True:
        func = misc.get_func(q.get())
        action[func]()
        time.sleep(0.1)


def main():
    if sys.argv[-1] == 'on':
        if top_board:
            oled.welcome()
    elif sys.argv[-1] == 'off':
        if top_board:
            oled.goodbye()
        exit(0)
        

if __name__ == '__main__':
    main()
    if top_board:
        p_key_processor = mp.Process(target=receive_key, args=(q,), name='Receive Key')
        p_key_processor.start()
        
        p_Key_decoder = mp.Process(target=misc.watch_key, args=(q,), name='Watch Key')
        p_Key_decoder.start()
        
        p_display_mamager = mp.Process(target=oled.auto_slider, name='Auto Slider', args=(display_queue,))
        p_display_mamager.start()
        
        p_display_process = mp.Process(target=oled.display_process, name='Display Process', args=(display_queue,))
        p_display_process.start()
        
        refresh_period = misc.get_refresh_period()
        if (refresh_period > refresh_theshold):
            p_refresh_display = mp.Process(target=oled.refresh_display, name='Refresh Display', args=(display_queue,))
            p_refresh_display.start()

    p_fan = mp.Process(target=fan.running, name='Fan')
    p_fan.start()
    
    p_fan.join()
