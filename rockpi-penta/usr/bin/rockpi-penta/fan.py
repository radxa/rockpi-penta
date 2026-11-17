#!/usr/bin/env python3
import os.path
import time
import traceback
import threading

import hatgpio
import misc
import temps

pin = None


class Pwm:
    def __init__(self, chip):
        self.period_value = None
        try:
            int(chip)
            chip = f'pwmchip{chip}'
        except ValueError:
            pass
        self.filepath = f"/sys/class/pwm/{chip}/pwm0/"
        try:
            with open(f"/sys/class/pwm/{chip}/export", 'w') as f:
                f.write('0')
        except OSError:
            print("Waring: init pwm error")
            traceback.print_exc()

    def period(self, ns: int):
        self.period_value = ns
        with open(os.path.join(self.filepath, 'period'), 'w') as f:
            f.write(str(ns))

    def period_us(self, us: int):
        self.period(us * 1000)

    def enable(self, t: bool):
        with open(os.path.join(self.filepath, 'enable'), 'w') as f:
            f.write(f"{int(t)}")

    def write(self, duty: float):
        assert self.period_value, "The Period is not set."
        with open(os.path.join(self.filepath, 'duty_cycle'), 'w') as f:
            f.write(f"{int(self.period_value * duty)}")


class Gpio:
    """Software PWM on a plain GPIO line.

    `write()` takes the fraction of each period the line stays low (see
    misc.duty2dc). At the ends of the range the line is held at a fixed level
    instead of pulsing, so "off" really is off and "full" really is full.
    """

    def _tr(self):
        line = hatgpio.OutputLine(self.gpio, self.line, consumer="fan")
        while True:
            high, low = self.value
            if low <= 0:
                line.set(True)
                time.sleep(self.period_s)
            elif high <= 0:
                line.set(False)
                time.sleep(self.period_s)
            else:
                line.set(True)
                time.sleep(high)
                line.set(False)
                time.sleep(low)

    def __init__(self, period_s):

        self.gpio = os.environ['FAN_CHIP']
        self.line = int(os.environ['FAN_LINE'])
        self.value = [period_s / 2, period_s / 2]
        self.period_s = period_s
        self.thread = threading.Thread(target=self._tr, daemon=True)
        self.thread.start()

    def write(self, duty):
        low = min(max(duty, 0.0), 1.0) * self.period_s
        self.value = [self.period_s - low, low]


CPU_INTERVAL = 10   # seconds between temperature reads
DISK_INTERVAL = 30  # disks warm up and cool down over minutes


def read_source(warned={}):
    """(temperature, levels, description) for the configured source.

    With source = disk the hottest selected disk is used, against the disk_lv*
    thresholds. When no disk can be read the CPU and its own thresholds take
    over, with a warning, so the fan is never left without a reference.
    """
    if misc.conf['fan']['source'] == 'disk':
        disks = temps.disk_temps(misc.conf['fan']['disks'])
        if disks:
            warned.pop('disk', None)
            hottest = max(disks, key=disks.get)
            return disks[hottest], 'disk_', f'{hottest} {disks[hottest]:.0f}°C'
        if not warned.get('disk'):
            warned['disk'] = True
            print("Warning: no disk temperature readable (is the drivetemp module "
                  "loaded?), following the CPU instead")
    t = temps.cpu_temp()
    return t, '', f'cpu {t:.0f}°C'


def get_dc(cache={}):
    if misc.conf['run'].value == 0:
        return misc.duty2dc(misc.FAN_DUTY_OFF)

    interval = DISK_INTERVAL if misc.conf['fan']['source'] == 'disk' else CPU_INTERVAL
    if time.time() - cache.get('time', 0) > interval:
        cache['time'] = time.time()
        t, levels, _ = read_source()
        cache['dc'] = misc.fan_temp2dc(t, levels)

    return cache['dc']


def change_dc(dc, cache={}):
    if dc != cache.get('dc'):
        cache['dc'] = dc
        pin.write(dc)


def running():
    global pin
    if os.environ['HARDWARE_PWM'] == '1':
        chip = os.environ['PWMCHIP']
        pin = Pwm(chip)
        pin.period_us(40)
        pin.enable(True)
    else:
        pin = Gpio(0.025)
    while True:

        dc = get_dc()
        change_dc(dc)
        time.sleep(1)


if __name__ == '__main__':
    running()
