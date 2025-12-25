# GPIOD v2 Migration - Quick Reference

## What was done?

I've successfully migrated your rockpi-penta project from GPIOD v1 to GPIOD v2 API in a new branch called `gpiod-v2-migration`.

## Current Branch Status

```
Current Branch: gpiod-v2-migration
Parent Branch: master
Status: Ready for testing
```

## Files Modified

1. **rockpi-penta/usr/bin/rockpi-penta/fan.py**
   - Updated `Gpio` class to use GPIOD v2 API
   - Changed line request and value operations

2. **rockpi-penta/usr/bin/rockpi-penta/misc.py**
   - Updated `read_key()` function to use GPIOD v2 API
   - Changed button GPIO handling

3. **rockpi-penta/DEBIAN/control**
   - Version bumped: 0.2 → 0.3
   - Added dependency: `python3-libgpiod (>= 2.0)`
   - Updated description

4. **GPIOD_V2_MIGRATION.md** (NEW)
   - Comprehensive migration notes
   - API comparison table
   - Testing checklist
   - Rollback instructions

## Next Steps

### 1. Switch to the new branch (already there):
```bash
git checkout gpiod-v2-migration
```

### 2. Test on your hardware:
```bash
# Check GPIOD version
python3 -c "import gpiod; print(gpiod.__version__)"

# Install/update if needed
sudo apt update
sudo apt install python3-libgpiod

# Test the service
sudo systemctl restart rockpi-penta
sudo journalctl -u rockpi-penta -f
```

### 3. Verify functionality:
- [ ] Fan control responds to temperature
- [ ] Fan speed levels work (lv0-lv3)
- [ ] Button single click works (slider)
- [ ] Button double click works (switch)
- [ ] Button long press works (if configured)
- [ ] OLED display updates correctly

### 4. If everything works, merge to master:
```bash
git checkout master
git merge gpiod-v2-migration
git push origin master
```

### 5. If issues arise, rollback:
```bash
git checkout master
# Your original code is safe!
```

## Key Differences (Quick Reference)

| Operation | GPIOD v1 | GPIOD v2 |
|-----------|----------|----------|
| **Open chip & line** | `gpiod.Chip(path).get_line(num)` | `gpiod.request_lines(path, config=...)` |
| **Request line** | `line.request(type=LINE_REQ_DIR_OUT)` | `LineSettings(direction=Direction.OUTPUT)` |
| **Set HIGH** | `line.set_value(1)` | `request.set_value(offset, Value.ACTIVE)` |
| **Set LOW** | `line.set_value(0)` | `request.set_value(offset, Value.INACTIVE)` |
| **Get value** | `line.get_value()` | `request.get_value(offset)` |

## Why GPIOD v2?

1. ✅ Modern, cleaner API design
2. ✅ Better resource management
3. ✅ Future-proof (v1 is deprecated)
4. ✅ Improved performance
5. ✅ Enhanced features support

## Questions?

Read the full migration notes in `GPIOD_V2_MIGRATION.md` for detailed information.

---
Generated: December 25, 2025
Branch: gpiod-v2-migration
Commit: 9ecdd08
