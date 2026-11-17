#!/usr/bin/env python3
"""GPIO access for the button and the software-PWM fan, on libgpiod 1 and 2.

Debian 12 ships python3-libgpiod 1.6 and Debian 13 ships 2.x, whose Python API
is entirely different. Everything that touches a line goes through this module
so the rest of the program does not care which one is installed.

A chip can be given as a path (/dev/gpiochip4), a number (4) or a label
(pinctrl-rp1). The label is the stable choice: the kernel is free to renumber
chips, and the Raspberry Pi 5 header moved from gpiochip4 to other numbers
between kernel releases.
"""
import glob
import os
import time
from datetime import timedelta

import gpiod

V2 = hasattr(gpiod, 'request_lines')


def _chip_label(path):
    if V2:
        with gpiod.Chip(path) as chip:
            return chip.get_info().label
    chip = gpiod.Chip(path, gpiod.Chip.OPEN_BY_PATH)
    try:
        return chip.label()
    finally:
        chip.close()


def resolve_chip(spec):
    """The /dev path of the chip named by a path, a number or a label."""
    spec = str(spec).strip()
    if spec.startswith('/dev/'):
        return spec
    if spec.isdigit():
        return f'/dev/gpiochip{spec}'
    if spec.startswith('gpiochip'):
        return f'/dev/{spec}'
    for path in sorted(glob.glob('/dev/gpiochip*')):
        try:
            if _chip_label(path) == spec:
                return os.path.realpath(path)
        except OSError:
            continue
    raise FileNotFoundError(f'no GPIO chip labelled {spec!r}')


class OutputLine:
    """One line driven as an output, low until told otherwise."""

    def __init__(self, chip, offset, consumer):
        self._offset = int(offset)
        path = resolve_chip(chip)
        if V2:
            self._req = gpiod.request_lines(path, consumer=consumer, config={
                self._offset: gpiod.LineSettings(
                    direction=gpiod.line.Direction.OUTPUT,
                    output_value=gpiod.line.Value.INACTIVE)})
        else:
            self._chip = gpiod.Chip(path, gpiod.Chip.OPEN_BY_PATH)
            self._line = self._chip.get_line(self._offset)
            self._line.request(consumer=consumer, type=gpiod.LINE_REQ_DIR_OUT,
                               default_vals=[0])

    def set(self, high):
        if V2:
            self._req.set_value(self._offset, gpiod.line.Value.ACTIVE if high
                                else gpiod.line.Value.INACTIVE)
        else:
            self._line.set_value(1 if high else 0)


class InputLine:
    """One line read as an input with edge events, pulled up by default."""

    def __init__(self, chip, offset, consumer, pull_up=True):
        self._offset = int(offset)
        path = resolve_chip(chip)
        if V2:
            bias = gpiod.line.Bias.PULL_UP if pull_up else gpiod.line.Bias.AS_IS
            self._req = gpiod.request_lines(path, consumer=consumer, config={
                self._offset: gpiod.LineSettings(
                    direction=gpiod.line.Direction.INPUT,
                    edge_detection=gpiod.line.Edge.BOTH,
                    bias=bias)})
        else:
            self._chip = gpiod.Chip(path, gpiod.Chip.OPEN_BY_PATH)
            self._line = self._chip.get_line(self._offset)
            flags = getattr(gpiod, 'LINE_REQ_FLAG_BIAS_PULL_UP', 0) if pull_up else 0
            self._line.request(consumer=consumer, type=gpiod.LINE_REQ_EV_BOTH_EDGES,
                               flags=flags)

    def value(self):
        if V2:
            return self._req.get_value(self._offset) == gpiod.line.Value.ACTIVE
        return bool(self._line.get_value())

    def wait(self, timeout):
        """Block until an edge arrives or `timeout` seconds pass (None waits for ever).
        Returns whether an edge arrived; pending edges are consumed."""
        if V2:
            if not self._req.wait_edge_events(None if timeout is None
                                              else timedelta(seconds=max(timeout, 0))):
                return False
            self._req.read_edge_events()
            return True
        if timeout is None:
            while not self._line.event_wait(sec=3600):
                pass
        else:
            whole = int(max(timeout, 0))
            if not self._line.event_wait(sec=whole, nsec=int((max(timeout, 0) - whole) * 1e9)):
                return False
        while self._line.event_wait(nsec=0):
            self._line.event_read()
        return True


def button_states(line, debounce=0.01):
    """Yield True (pressed) / False (released) on every debounced change, and None
    whenever `timeout` passes without one. Send the next timeout in seconds (or
    None to wait for ever) with generator.send().

    The button pulls the line low, so pressed means the line reads low. Each edge
    is followed by a short settle time and the level is read afterwards, which
    filters contact bounce the same way on both libgpiod versions.
    """
    pressed = not line.value()
    timeout = None
    while True:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                timeout = yield None
                break
            if not line.wait(remaining):
                continue
            time.sleep(debounce)
            while line.wait(0):
                time.sleep(debounce)
            now_pressed = not line.value()
            if now_pressed != pressed:
                pressed = now_pressed
                timeout = yield pressed
                break
