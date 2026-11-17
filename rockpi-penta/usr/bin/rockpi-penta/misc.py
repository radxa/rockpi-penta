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


CONF_FILE = '/etc/rockpi-penta.conf'

# section, key, default, type, older names still accepted
CONF_KEYS = [
    ('fan', 'lv0', 35.0, float, ()),
    ('fan', 'lv1', 40.0, float, ()),
    ('fan', 'lv2', 45.0, float, ()),
    ('fan', 'lv3', 50.0, float, ()),
    ('fan', 'source', 'cpu', str, ()),
    ('fan', 'disks', 'auto', str, ()),
    ('fan', 'disk_lv0', 35.0, float, ()),
    ('fan', 'disk_lv1', 40.0, float, ()),
    ('fan', 'disk_lv2', 43.0, float, ()),
    ('fan', 'disk_lv3', 46.0, float, ()),
    ('fan', 'pwm_freq', 100.0, float, ()),
    ('key', 'click', 'slider', str, ()),
    ('key', 'twice', 'switch', str, ()),
    ('key', 'press', 'none', str, ()),
    ('time', 'twice', 0.7, float, ()),
    ('time', 'press', 1.8, float, ()),
    ('oled', 'rotate', False, bool, ()),
    ('oled', 'f-temp', False, bool, ()),
    ('oled', 'auto_slide', True, bool, (('slider', 'auto'),)),
    ('oled', 'auto_slide_time', 10.0, float, (('slider', 'time'),)),
    ('oled', 'sleep', 0.0, float, ()),
]


def _read_value(cfg, section, key, kind):
    if kind is bool:
        return cfg.getboolean(section, key)
    if kind is float:
        return cfg.getfloat(section, key)
    return cfg.get(section, key).strip()


def read_conf(path=CONF_FILE):
    """Read the configuration key by key.

    A missing or invalid key falls back to its own default and is reported, so a
    configuration file written for an older version keeps the values it has
    instead of being discarded as a whole.
    """
    conf = defaultdict(dict)
    cfg = ConfigParser()
    try:
        cfg.read(path)
    except Exception:
        traceback.print_exc()

    for section, key, default, kind, old_names in CONF_KEYS:
        value = default
        for sec, name in ((section, key),) + tuple(old_names):
            if not cfg.has_option(sec, name):
                continue
            try:
                value = _read_value(cfg, sec, name, kind)
            except ValueError:
                print(f"Warning: [{sec}] {name} in {path} is not valid, using {default}")
            break
        conf[section][key] = value

    source = conf['fan']['source'].lower()
    if source not in ('cpu', 'disk'):
        print(f"Warning: [fan] source = {source} in {path} is not cpu or disk, using cpu")
        source = 'cpu'
    conf['fan']['source'] = source
    disks = conf['fan']['disks'].lower()
    conf['fan']['disks'] = disks if disks in ('auto', 'all') else disks.replace(',', ' ').split()
    freq = conf['fan']['pwm_freq']
    if not 1 <= freq <= 1000:
        print(f"Warning: [fan] pwm_freq = {freq:g} in {path} is outside 1-1000 Hz, using 100")
        conf['fan']['pwm_freq'] = 100.0

    extra_disks = cfg.get('disk', 'extra', fallback="").strip()
    conf['disk'] = [d.strip() for d in extra_disks.split(",") if d.strip()] if extra_disks else []

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

def fan_temp2dc(t, levels=''):
    """Fan setting for temperature t, against the lv0..lv3 thresholds
    (levels='') or the disk_lv0..disk_lv3 ones (levels='disk_')."""
    result = FAN_DUTY_OFF
    for lv, dc in lv2dc.items():
        if t >= conf['fan'][levels + lv]:
            result = dc
            break

    return duty2dc(result)


def fan_switch():
    conf['run'].value = not conf['run'].value


def get_func(key):
    return conf['key'].get(key, 'none')


conf = {'disk': [], 'run': mp.Value('d', 1)}
conf.update(read_conf())
