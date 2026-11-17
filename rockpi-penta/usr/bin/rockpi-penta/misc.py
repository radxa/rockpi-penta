#!/usr/bin/env python3
import re
import os
import time
import subprocess
import multiprocessing as mp
import traceback

import hatgpio
from configparser import ConfigParser
from collections import defaultdict, OrderedDict

cmds = {
    'blk': "lsblk | awk '{print $1}'",
    'up': "echo Uptime: `uptime | sed 's/.*up \\([^,]*\\), .*/\\1/'`",
    'temp': "cat /sys/class/thermal/thermal_zone0/temp",
    'ip': "hostname -I | awk '{printf \"IP %s\", $1}'",
    'cpu': "uptime | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'",
    'men': "free -m | awk 'NR==2{printf \"Mem: %s/%sMB\", $3,$2}'",
    'disk': "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
}

FAN_DUTY_OFF = 0.0
FAN_DUTY_ON  = 1.0 
lv2dc = OrderedDict({'lv3': 1.0, 'lv2':0.75, 'lv1': 0.5, 'lv0': 0.25})
duty2dc = lambda x: 1.0 - x




def check_output(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()


def check_call(cmd):
    return subprocess.check_call(cmd, shell=True)


def get_blk():
    conf['disk'] = [x for x in check_output(cmds['blk']).strip().split('\n') if x.startswith('sd')]


def get_info(s):
    return check_output(cmds[s])


def get_cpu_temp():
    t = float(get_info('temp')) / 1000
    if conf['oled']['f-temp']:
        temp = "CPU Temp: {:.0f}°F".format(t * 1.8 + 32)
    else:
        temp = "CPU Temp: {:.1f}°C".format(t)
    return temp


def read_conf():
    conf = defaultdict(dict)

    try:
        cfg = ConfigParser()
        cfg.read('/etc/rockpi-penta.conf')
        # fan
        conf['fan']['lv0'] = cfg.getfloat('fan', 'lv0')
        conf['fan']['lv1'] = cfg.getfloat('fan', 'lv1')
        conf['fan']['lv2'] = cfg.getfloat('fan', 'lv2')
        conf['fan']['lv3'] = cfg.getfloat('fan', 'lv3')
        # key
        conf['key']['click'] = cfg.get('key', 'click')
        conf['key']['twice'] = cfg.get('key', 'twice')
        conf['key']['press'] = cfg.get('key', 'press')
        # time
        conf['time']['twice'] = cfg.getfloat('time', 'twice')
        conf['time']['press'] = cfg.getfloat('time', 'press')
        # other

        conf['oled']['rotate'] = cfg.getboolean('oled', 'rotate')
        conf['oled']['f-temp'] = cfg.getboolean('oled', 'f-temp')
        conf['oled']['auto_slide'] = cfg.getboolean('oled', 'auto_slide')
        conf['oled']['auto_slide_time'] = cfg.getfloat('oled', 'auto_slide_time')
        conf['oled']['sleep'] = cfg.getfloat('oled', 'sleep')

        extra_disks = cfg.get('disk', 'extra', fallback="")
        if extra_disks != "":
            extra_disks = extra_disks.split(",")
        conf["disk"] = extra_disks

    except Exception:
        traceback.print_exc()
        # fan
        conf['fan']['lv0'] = 35
        conf['fan']['lv1'] = 40
        conf['fan']['lv2'] = 45
        conf['fan']['lv3'] = 50
        # key
        conf['key']['click'] = 'slider'
        conf['key']['twice'] = 'switch'
        conf['key']['press'] = 'none'
        # time
        conf['time']['twice'] = 0.7  # second
        conf['time']['press'] = 1.8
        # other
        conf['oled']['rotate'] = False
        conf['oled']['f-temp'] = False
        conf['oled']['auto_slide'] = True
        conf['oled']['auto_slide_time'] = 10  # second
        conf['oled']['sleep'] = 0  # second

    return conf


def read_key_events(chip_device, chip_line):
    """Turn button presses into 'click', 'twice' and 'press' events.

    Written by Igor Petrov for libgpiod 2 (event based instead of polling); it now
    runs on hatgpio, so the same logic works on libgpiod 1 as well.
    """
    time_long_press = float(conf['time']['press'])
    time_double_click = float(conf['time']['twice'])

    line = hatgpio.InputLine(chip_device, chip_line, consumer="hat_button")
    states = hatgpio.button_states(line)

    click_count = 0
    wait = None
    ignore_release = False
    state = next(states)

    while True:
        if state is None:  # the wait ran out
            if click_count == 0:
                ignore_release = True
                yield "press"
            if click_count == 1:
                yield "click"
            click_count = 0
            wait = None
        elif state:  # pressed
            if click_count == 0:  # arm long press detection
                wait = time_long_press
        else:  # released
            if ignore_release:
                ignore_release = False
            else:
                click_count += 1
                if click_count == 1:
                    wait = time_double_click
                if click_count == 2 and wait == time_double_click:
                    click_count = 0
                    wait = None
                    yield "twice"
        state = states.send(wait)


def watch_key(q=None):

    chip_device = os.environ['BUTTON_CHIP']
    chip_line = os.environ['BUTTON_LINE']

    for key_event in read_key_events(chip_device, chip_line):
        q.put(key_event)


def get_disk_info(cache={}):
    if not cache.get('time') or time.time() - cache['time'] > 30:
        info = {}
        cmd = "df -h | awk '$NF==\"/\"{printf \"%s\", $5}'"
        info['root'] = check_output(cmd)
        for x in conf['disk']:
            cmd = "df -Bg | awk '$1==\"/dev/{}\" {{printf \"%s\", $5}}'".format(x)
            info[x] = check_output(cmd)
        cache['info'] = list(zip(*info.items()))
        cache['time'] = time.time()

    return cache['info']

def get_slide_active():
    return conf['oled']['auto_slide']

def get_slide_time():
    return conf['oled']['auto_slide_time']

def get_sleep_time():
    return conf['oled']['sleep']

def fan_temp2dc(t):

    result = FAN_DUTY_OFF
    for lv, dc in lv2dc.items():
        if t >= conf['fan'][lv]:
            result = dc
            break

    #print(f"t = {t:.3f}°C -> {result:.3f}")

    duty = duty2dc(result)

    return duty


def fan_switch():
    conf['run'].value = not conf['run'].value


def get_func(key):
    return conf['key'].get(key, 'none')


conf = {'disk': [], 'run': mp.Value('d', 1)}
conf.update(read_conf())
