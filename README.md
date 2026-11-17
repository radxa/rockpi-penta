# ROCK Pi Penta SATA

Top Board control program for the Radxa Penta SATA HAT: the OLED display, the
button and the fan.

[Penta SATA HAT wiki](<https://wiki.radxa.com/Penta_SATA_HAT>)

[Penta SATA HAT docs](https://docs.radxa.com/en/accessories/penta-sata-hat)

![penta-hat](images/penta-sata-hat.png)

## What this fork adds

On top of [Radxa's program](https://github.com/radxa/rockpi-penta):

* **Event-based button**: the program sleeps until the button changes instead
  of polling it ten times a second, and no longer misses short presses.
* **OLED sleep mode**: the display blanks after a while without button presses
  to avoid burn-in; the first press wakes it up.
* **Fan driven by the disks or the CPU**: the fan blows over the disks, so it
  can follow the hottest disk instead of the CPU temperature.
* **All four fan speeds work**: the software PWM runs at a configurable
  frequency (100 Hz by default) instead of a fixed 40 Hz, at which the fan
  stalled below 75%.
* **Debian 12 and 13**: runs on both libgpiod 1 (Debian 12, bookworm) and
  libgpiod 2 (Debian 13, trixie).
* **Stable GPIO naming on the Raspberry Pi 5**: the header chip is looked up by
  its label, so kernel updates that renumber GPIO chips do not break it.
* The configuration is read key by key, so files written for older versions
  keep working, and it survives package upgrades.

## Configuration

Everything lives in `/etc/rockpi-penta.conf`; restart the service after editing
it: `sudo systemctl restart rockpi-penta`.

### Fan

```ini
[fan]
source = disk     # disk: follow the hottest disk; cpu: follow the CPU
disks = auto      # auto (spinning disks only), all, or names: sda sdb
lv0 = 35          # CPU thresholds, 'C: 25% / 50% / 75% / 100% above each
lv1 = 40
lv2 = 45
lv3 = 50
disk_lv0 = 35     # disk thresholds, 'C
disk_lv1 = 40
disk_lv2 = 43
disk_lv3 = 46
pwm_freq = 100    # software PWM frequency, Hz
```

Below the first threshold the fan is off. On boards without hardware PWM (such
as the Raspberry Pi) the fan is pulsed in software; at the original 40 Hz the
HAT fan stalls below 75% power, so the default is now 100 Hz, where it runs
from 25%. Raise or lower `pwm_freq` if your fan stalls or whines. Disk temperatures are read from the
kernel's `drivetemp` driver, which the package loads at boot; if no disk can be
read, the fan follows the CPU with the CPU thresholds.

### Button

```ini
[key]
click = slider    # slider: next page; switch: fan on/off; reboot; poweroff; none
twice = switch
press = none

[time]
twice = 0.7       # maximum seconds between the two presses of a double click
press = 1.8       # seconds held for a long press
```

### Display

```ini
[oled]
rotate = false          # turn the text 180 degrees
f-temp = false          # Fahrenheit
auto_slide = false      # change page on its own
auto_slide_time = 10    # seconds per page
sleep = 60              # blank after this many seconds without a press (0: never)
```

## Credits

* [Radxa](https://github.com/radxa/rockpi-penta): the original program.
* Igor Petrov ([Pudel-des-Todes/rockpi-penta](https://github.com/Pudel-des-Todes/rockpi-penta)):
  libgpiod 2 support, event-based button handling, the OLED sleep mode, the
  venv installation, the extra disks on the display and the fan duty fixes.
  His commits are merged here with their history.
* The disk temperature fan source was prompted by SergeyZa's proposal in
  [radxa/rockpi-penta#28](https://github.com/radxa/rockpi-penta/pull/28); the
  implementation here is a separate one, based on drivetemp.

Released under the MIT License, see [LICENSE](LICENSE).
