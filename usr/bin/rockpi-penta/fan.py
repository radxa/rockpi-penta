#!/usr/bin/env python3
"""
Control the PENTA HAT top fan according to the temperature of the RockPi.
We really should read the top hat temperature (as with the SATA HAT code).

Uses the mraa GPIO library for PWM.
   : https://iotdk.intel.com/docs/master/mraa/python/mraa.html#pwm
   PWM ratio is in range of 0.0 to 1.0 - it is the off ratio, rather than on ratio

Fan PWN frequency is 25KHz, according to Noctua fan white paper
   : https://noctua.at/pub/media/wysiwyg/Noctua_PWM_specifications_white_paper.pdf

"""

import time
import mraa  # pylint: disable=import-error
import misc

fan_pin = 13

pin13 = mraa.Pwm(fan_pin)
pin13.period_us(40)
pin13.enable(True)


"""
    Read the CPU temperature and include disks if we want
    to use their temperature as well. This means that we
    have to be capturing disk temperatures (auto display).
"""
def read_cpu_temp():
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        t_cpu = float(f.read().strip()) / 1000.0
        if misc.is_temp_farenheit():
            t_cpu = t_cpu *1.8 + 32
    if misc.is_fan_cpu_and_disk():
        if (misc.get_last_disk_temp_poll() + misc.get_fan_poll_delay()) < time.time():    # poll disk temps
            misc.get_disk_temp_info()
        t_disk = misc.get_disk_temp_average()
    else:
        t_disk = 0.0
    cpu_temp = max(t_cpu, t_disk)
    return cpu_temp


"""
    Return the speed % the top_board fan.
"""
def get_dc(cache={}):
    if not(misc.fan_running()):
        return 0.1      # 0.0% can make fan run faster

    # limit the update rate to once every 5 seconds
    if time.time() - cache.get('time', 0) > 5:
        cache['time'] = time.time()
        cache['dc'] = misc.fan_temp2dc(read_cpu_temp())
    return cache['dc']

"""
    Change the PWM off ratio for the fan if it changed.
    We receive a percent and need a 0.0 to 1.0 off ratio.
"""
def change_dc(dc, cache={}):
    if dc != cache.get('dc'):
        cache['dc'] = dc
        pin13.write(1 - (dc / 100))

"""
    Main loop updating the fan's speed according to the
    desired temperature thresholds.
"""
def running():
    while True:
        change_dc(get_dc())
        time.sleep(0.1)
