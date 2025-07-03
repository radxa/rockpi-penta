#!/usr/bin/env python3
import os
import os.path
import time
import traceback
import threading

import gpiod

import misc

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
    def __init__(self, period_s):
        self.is_zero_duty = False 
        try:
            fan_chip_env = os.environ.get('FAN_CHIP', '0') 
            fan_line_env = os.environ.get('FAN_LINE', '27') 
            
            self.chip_obj = gpiod.Chip(fan_chip_env)
            self.line = self.chip_obj.get_line(int(fan_line_env))
            self.line.request(consumer='fan', type=gpiod.LINE_REQ_DIR_OUT)
            
            self.value = [period_s / 2.0, period_s / 2.0] 
            self.period_s = period_s
            self.thread = threading.Thread(target=self.tr, daemon=True)
            self.thread.start()
        except Exception as e_gpio_init:
            raise 

    def tr(self):
        try:
            while True:
                if self.is_zero_duty: 
                    self.line.set_value(0) 
                    time.sleep(self.period_s) 
                else:
                    high_sleep = max(0.0, self.value[0])
                    low_sleep = max(0.0, self.value[1])
                    if high_sleep + low_sleep < self.period_s * 0.9: # Heuristic for significant difference
                       low_sleep = self.period_s - high_sleep
                       low_sleep = max(0.0, low_sleep) # Ensure non-negative

                    self.line.set_value(1)
                    time.sleep(high_sleep) 
                    self.line.set_value(0)
                    time.sleep(low_sleep) 
        except Exception as e_tr:
            pass 

    def write(self, duty: float):
        if not hasattr(self, 'line'):
            return 

        if duty <= 0.001:  # Treat near-zero as zero
            self.is_zero_duty = True
            self.value[0] = 0.0 
            self.value[1] = self.period_s 
        else:
            self.is_zero_duty = False
            duty = min(duty, 1.0) # Hard code duty cycle at 1.0
            self.value[0] = duty * self.period_s
            self.value[1] = self.period_s - self.value[0]

def read_temp():
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        t = int(f.read().strip()) / 1000.0
    return t


def get_dc(cache={}):
    if misc.conf['run'].value == 0:
        return 0.999

    if time.time() - cache.get('time', 0) > 60:
        cache['time'] = time.time()
        cache['dc'] = misc.fan_temp2dc(read_temp())

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
        change_dc(get_dc())
        time.sleep(1)


if __name__ == '__main__':
    running()
