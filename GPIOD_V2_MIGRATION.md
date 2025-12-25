# GPIOD v2 Migration Notes

## Overview
This branch (`gpiod-v2-migration`) contains the migration from GPIOD v1 to GPIOD v2 API.

## Changes Made

### 1. fan.py - Gpio class
**GPIOD v1 (old):**
```python
self.line = gpiod.Chip(os.environ['FAN_CHIP']).get_line(int(os.environ['FAN_LINE']))
self.line.request(consumer='fan', type=gpiod.LINE_REQ_DIR_OUT)
self.line.set_value(1)
self.line.set_value(0)
```

**GPIOD v2 (new):**
```python
chip_path = os.environ['FAN_CHIP']
line_offset = int(os.environ['FAN_LINE'])

self.line_request = gpiod.request_lines(
    chip_path,
    consumer='fan',
    config={
        line_offset: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.INACTIVE
        )
    }
)

self.line_request.set_value(line_offset, gpiod.line.Value.ACTIVE)
self.line_request.set_value(line_offset, gpiod.line.Value.INACTIVE)
```

### 2. misc.py - read_key function
**GPIOD v1 (old):**
```python
chip = gpiod.Chip(str(CHIP_NAME))
line = chip.get_line(int(LINE_NUMBER))
line.request(consumer='hat_button', type=gpiod.LINE_REQ_DIR_OUT)
line.set_value(1)
value = line.get_value()
```

**GPIOD v2 (new):**
```python
LINE_NUMBER = int(os.environ['BUTTON_LINE'])

line_request = gpiod.request_lines(
    CHIP_NAME,
    consumer='hat_button',
    config={
        LINE_NUMBER: gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            bias=gpiod.line.Bias.PULL_UP
        )
    }
)

# IMPORTANT: get_value() returns Value enum, not int
value = line_request.get_value(LINE_NUMBER)
# Convert: Value.ACTIVE = 1, Value.INACTIVE = 0
int_value = 1 if value == gpiod.line.Value.ACTIVE else 0
```

### 3. DEBIAN/control
- Updated version from 0.2 to 0.3
- Added minimum version requirement for python3-libgpiod (>= 2.0)
- Updated description to indicate GPIOD v2 support

## Key API Differences

| GPIOD v1 | GPIOD v2 |
|----------|----------|
| `gpiod.Chip()` + `get_line()` | `gpiod.request_lines()` |
| `line.request(type=gpiod.LINE_REQ_DIR_OUT)` | `gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT)` |
| `line.request(type=gpiod.LINE_REQ_DIR_IN)` | `gpiod.LineSettings(direction=gpiod.line.Direction.INPUT)` |
| `line.set_value(1)` / `line.set_value(0)` | `line_request.set_value(offset, gpiod.line.Value.ACTIVE/INACTIVE)` |
| `line.get_value()` returns `int` | `line_request.get_value(offset)` returns `Value` enum |

## Important Notes

### Value Enum Handling
In GPIOD v2, `get_value()` returns a `gpiod.line.Value` enum, NOT an integer:
- `Value.ACTIVE` = logical high (1)
- `Value.INACTIVE` = logical low (0)

You must convert explicitly:
```python
value = line_request.get_value(offset)
int_value = 1 if value == gpiod.line.Value.ACTIVE else 0
```

### GPIO Direction
- **OUTPUT**: For controlling devices (fan, LEDs, etc.)
- **INPUT**: For reading sensors, buttons, etc.
- Remember to set appropriate bias for inputs: `bias=gpiod.line.Bias.PULL_UP` or `PULL_DOWN`

## Testing Requirements

Before merging this branch, please test:

1. **Fan Control**: Verify the fan responds correctly to temperature changes
   - Test all fan speed levels (lv0-lv3)
   - Verify PWM control works correctly
   - Test fan switch functionality

2. **Button Control**: Verify the button responds correctly
   - Test single click (slider)
   - Test double click (switch)
   - Test long press (configurable action)

3. **System Integration**:
   - Verify systemd service starts correctly
   - Check for any error messages in logs: `journalctl -u rockpi-penta`
   - Test on target hardware (Rock Pi, etc.)

## Installation Notes

Ensure your system has GPIOD v2 library installed:
```bash
# Check version
python3 -c "import gpiod; print(gpiod.__version__)"

# If needed, update libgpiod
sudo apt update
sudo apt install python3-libgpiod
```

## Rollback

If you encounter issues, you can switch back to the master branch:
```bash
git checkout master
```

## Benefits of GPIOD v2

1. **Modern API**: GPIOD v2 provides a cleaner, more object-oriented API
2. **Better Resource Management**: Improved handling of GPIO resources
3. **Enhanced Features**: Support for additional GPIO features and configurations
4. **Future-proof**: GPIOD v1 is deprecated and v2 is the recommended version
5. **Improved Performance**: Better performance and lower overhead

## Notes

- The GPIOD v2 API is not backwards compatible with v1
- All GPIO operations have been updated to use the new API
- The functionality remains the same, only the implementation has changed
