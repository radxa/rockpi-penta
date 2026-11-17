#!/usr/bin/env python3
"""Temperatures the fan can follow: the CPU, or the disks behind the HAT.

Disk temperatures come from the kernel's drivetemp hwmon driver, the same value
SMART reports but read from sysfs, without running smartctl.
"""
import glob
import os


def cpu_temp():
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        return int(f.read().strip()) / 1000.0


def _disk_of(hwmon):
    """The block device name (sda...) behind a drivetemp hwmon entry, or None."""
    blocks = glob.glob(os.path.join(hwmon, 'device', 'block', '*'))
    return os.path.basename(blocks[0]) if blocks else None


def _rotational(disk):
    try:
        with open(f'/sys/block/{disk}/queue/rotational') as f:
            return f.read().strip() == '1'
    except OSError:
        return False


def disk_temps(selection='auto'):
    """{disk: °C} for the disks drivetemp can read.

    selection: 'auto' for spinning disks only (SSDs run hotter by design and
    would drive the fan for nothing), 'all' for every disk, or a list of names
    such as ['sda', 'sdb']. Disks that cannot be read are left out.
    """
    temps = {}
    for hwmon in sorted(glob.glob('/sys/class/hwmon/hwmon*')):
        try:
            with open(os.path.join(hwmon, 'name')) as f:
                if f.read().strip() != 'drivetemp':
                    continue
            disk = _disk_of(hwmon)
            if disk is None:
                continue
            if selection == 'auto' and not _rotational(disk):
                continue
            if selection not in ('auto', 'all') and disk not in selection:
                continue
            with open(os.path.join(hwmon, 'temp1_input')) as f:
                temps[disk] = int(f.read().strip()) / 1000.0
        except (OSError, ValueError):
            continue
    return temps
