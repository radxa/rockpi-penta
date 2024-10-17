#!/usr/bin/env python3
import queue
import threading
import traceback

import fan
import misc

try:
    import oled

    top_board = True
except Exception as ex:
    traceback.print_exc()
    top_board = False

q = queue.Queue()
lock = threading.Lock()

action = {
    'none': lambda: 'nothing',
    'slider': lambda: oled.slider(lock),
    'switch': lambda: misc.fan_switch(),
    'reboot': lambda: misc.check_call('reboot'),
    'poweroff': lambda: misc.check_call('poweroff'),
}


def receive_key(q):
    while True:
        func = misc.get_func(q.get())
        action[func]()


if __name__ == '__main__':

    if top_board:
        oled.welcome()
        p0 = threading.Thread(target=receive_key, args=(q,), daemon=True)
        p1 = threading.Thread(target=misc.watch_key, args=(q,), daemon=True)
        p2 = threading.Thread(target=oled.auto_slider, args=(lock,), daemon=True)
        p3 = threading.Thread(target=fan.running, daemon=True)

        p0.start()
        p1.start()
        p2.start()
        p3.start()
        try:
            p3.join()
        except KeyboardInterrupt:
            misc.conf['run'].value = 0
            print("GoodBye ~")
            oled.goodbye()

    else:
        p3 = threading.Thread(target=fan.running, daemon=False)
        p3.start()
