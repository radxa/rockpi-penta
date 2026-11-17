#!/usr/bin/python3
import os
import time

import adafruit_ssd1306
import board
import digitalio
import busio
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import multiprocessing as mp
import threading

import misc

font = {
    '10': ImageFont.truetype('fonts/DejaVuSansMono.ttf', 10),
    '11': ImageFont.truetype('fonts/DejaVuSansMono.ttf', 11),
    '12': ImageFont.truetype('fonts/DejaVuSansMono.ttf', 12),
    '14': ImageFont.truetype('fonts/DejaVuSansMono.ttf', 14),
}


def disp_init():
    RESET = getattr(board.pin, os.environ['OLED_RESET'])
    i2c = busio.I2C(getattr(board.pin, os.environ['SCL']), getattr(board.pin, os.environ['SDA']))
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=digitalio.DigitalInOut(RESET))
    disp.fill(0)
    disp.show()
    return disp


disp = disp_init()

image = Image.new('1', (disp.width, disp.height))
draw = ImageDraw.Draw(image)


def disp_show():
    im = image.rotate(180) if misc.conf['oled']['rotate'] else image
    disp.image(im)
    disp.write_framebuf()
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)


def welcome():
    draw.text((0, 0), 'ROCKPi SATA HAT', font=font['14'], fill=255)
    draw.text((32, 16), 'Loading...', font=font['12'], fill=255)
    disp_show()


def goodbye():
    draw.text((32, 8), 'Good Bye ~', font=font['14'], fill=255)
    disp_show()
    time.sleep(2)
    disp_show()  # clear


def put_disk_info():
    k, v = misc.get_disk_info()
    text1 = '{} {}'.format(k[0], v[0])

    l = len(k)
    if l > 3:
        text2 = '{} {}  {} {}'.format(k[1], v[1], k[2], v[2])
        text3 = '{} {}'.format(k[3], v[3])
        if l > 4:
            text3 += '{} {}'.format(k[4], v[4])
        page = [
            {'xy': (0, -2), 'text': text1, 'fill': 255, 'font': font['11']},
            {'xy': (0, 10), 'text': text2, 'fill': 255, 'font': font['11']},
            {'xy': (0, 21), 'text': text3, 'fill': 255, 'font': font['11']},
        ]
    elif l > 1:
        text2 = '{} {}'.format(k[1], v[1])
        if l > 2:
            text2 += '{} {}'.format(k[2], v[2])
        page = [
            {'xy': (0, 2), 'text': text1, 'fill': 255, 'font': font['12']},
            {'xy': (0, 18), 'text': text2, 'fill': 255, 'font': font['12']},
        ]
    else:
        page = [{'xy': (0, 2), 'text': text1, 'fill': 255, 'font': font['14']}]

    return page



def gen_pages(idx):

    if idx == 0:
        return [
            {'xy': (0, -2), 'text': misc.get_info('up'), 'fill': 255, 'font': font['11']},
            {'xy': (0, 10), 'text': misc.get_cpu_temp(), 'fill': 255, 'font': font['11']},
            {'xy': (0, 21), 'text': misc.get_info('ip'), 'fill': 255, 'font': font['11']},
        ]
    elif idx == 1:
        return [
            {'xy': (0, 2), 'text': misc.get_info('cpu'), 'fill': 255, 'font': font['12']},
            {'xy': (0, 18), 'text': misc.get_info('men'), 'fill': 255, 'font': font['12']},
        ]
    else:
        return put_disk_info()



idx = -1
is_blank = False

def blank():
    global idx, is_blank

    if not is_blank:
        disp_show()
        
    idx = -1
    is_blank = True

def refresh(next_page = False):


    global idx, is_blank

    if next_page:
        idx += 1
        idx %= 3

    for item in gen_pages(idx):
        draw.text(**item)
    disp_show()

    is_blank = False

def auto_slider(slide_event):

    last_event = time.monotonic()
    sleep_time = misc.get_sleep_time()
    slide_time = misc.get_slide_time()

    slide = True
    while True:
        now = time.monotonic()

        if slide:
            last_event = now

        if sleep_time > 0 and now - last_event > sleep_time:
            blank()
        elif misc.get_slide_active() or slide:
            refresh(True)
        else:
            refresh()
        slide_event.clear()
        slide_event.wait(slide_time)
        slide = slide_event.is_set()

if __name__ == '__main__':
    # for test
    event = threading.Event()
    auto_slider(event)
