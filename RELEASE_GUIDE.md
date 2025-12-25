# RockPi Penta Hat - GPIOD v2 Release Guide

## 🚀 Quick Installation

```bash
# 1. Clone or pull the latest code
git clone -b gpiod-v2-migration https://github.com/aldrineeinsteen/rockpi-penta.git
cd rockpi-penta

# 2. Make scripts executable
chmod +x build-deb.sh install.sh

# 3. Run the installer (builds and installs)
./install.sh
```

## 📦 Manual Build & Install

### Build the DEB Package
```bash
# Make build script executable
chmod +x build-deb.sh

# Build the package
./build-deb.sh
```

This creates: `rockpi-penta_0.3_all.deb`

### Install the Package
```bash
# Install
sudo dpkg -i rockpi-penta_0.3_all.deb

# Fix dependencies if needed
sudo apt-get install -f
```

## 🔧 Service Management

### Check Service Status
```bash
sudo systemctl status rockpi-penta
```

### View Live Logs
```bash
sudo journalctl -u rockpi-penta -f
```

### Control the Service
```bash
sudo systemctl start rockpi-penta    # Start
sudo systemctl stop rockpi-penta     # Stop
sudo systemctl restart rockpi-penta  # Restart
sudo systemctl enable rockpi-penta   # Enable on boot
sudo systemctl disable rockpi-penta  # Disable on boot
```

## ⚙️ Configuration

### Main Configuration
Edit `/etc/rockpi-penta.conf` for user preferences:
```ini
[fan]
lv0 = 35
lv1 = 40
lv2 = 45
lv3 = 50

[key]
click = slider
twice = switch
press = none

[time]
twice = 0.7
press = 1.8

[slider]
auto = True
time = 10

[oled]
rotate = False
f-temp = False
```

### Hardware Configuration
Hardware-specific settings are in `/etc/rockpi-penta.env` (auto-generated based on your board):
```bash
# Example for Raspberry Pi 5
BUTTON_CHIP=4
BUTTON_LINE=17
FAN_CHIP=4
FAN_LINE=27
HARDWARE_PWM=0
SDA=SDA
SCL=SCL
OLED_RESET=D23
```

**Note:** The env file is automatically created during installation. Only modify if you need custom GPIO pin assignments.

## 🔍 Troubleshooting

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u rockpi-penta -n 50 --no-pager

# Check GPIOD version (must be >= 2.0)
python3 -c "import gpiod; print(gpiod.__version__)"

# Test manually
sudo systemctl stop rockpi-penta
cd /usr/bin/rockpi-penta
sudo python3 main.py
```

### Update GPIOD to v2
```bash
sudo apt update
sudo apt install --only-upgrade python3-libgpiod

# Verify version
python3 -c "import gpiod; print(gpiod.__version__)"
```

### Permission Issues
```bash
# Check if user is in gpio group (if applicable)
groups

# Add user to gpio group
sudo usermod -a -G gpio $USER
```

## 🗑️ Uninstallation

```bash
# Using apt
sudo apt remove rockpi-penta

# Or using dpkg
sudo dpkg -r rockpi-penta
```

## 📋 What's Included

The DEB package installs:
- Python scripts → `/usr/bin/rockpi-penta/`
- Systemd service → `/lib/systemd/system/rockpi-penta.service`
- Configuration → `/etc/rockpi-penta.conf`
- Environment templates → `/usr/bin/rockpi-penta/env/*.env`
- Fonts → `/usr/bin/rockpi-penta/fonts/`
- Device tree overlays → `/usr/bin/rockpi-penta/overlays/`

## 📝 Post-Installation

The package automatically:
1. ✅ Detects your board model
2. ✅ Installs Python dependencies
3. ✅ Configures environment variables
4. ✅ Enables the systemd service
5. ✅ Starts the service (on supported boards)
6. ✅ Configures device tree overlays (if needed)

## 🔄 Upgrading from v1

If you're upgrading from GPIOD v1:
1. The new package will automatically replace the old one
2. Ensure libgpiod v2 is installed
3. Service will be restarted automatically

## 🎯 Supported Boards

- Raspberry Pi 4
- Raspberry Pi 5
- Rock Pi 4 / 4SE
- Rock Pi 3 / 3A / 3C
- Rock 5A

## 📦 Creating a Release

### For Repository Maintainers

1. **Build the package:**
   ```bash
   ./build-deb.sh
   ```

2. **Test on target hardware:**
   ```bash
   ./install.sh
   sudo systemctl status rockpi-penta
   ```

3. **Tag the release:**
   ```bash
   git tag -a v0.3-gpiod-v2 -m "GPIOD v2 release"
   git push origin v0.3-gpiod-v2
   ```

4. **Create GitHub Release:**
   - Go to: https://github.com/aldrineeinsteen/rockpi-penta/releases/new
   - Tag: `v0.3-gpiod-v2`
   - Title: `RockPi Penta Hat v0.3 - GPIOD v2`
   - Attach: `rockpi-penta_0.3_all.deb`
   - Description: See `GPIOD_V2_MIGRATION.md`

5. **Upload to package repository (optional):**
   ```bash
   # For APT repository
   reprepro includedeb stable rockpi-penta_0.3_all.deb
   ```

## 📚 Documentation

- **Migration Guide**: `GPIOD_V2_MIGRATION.md` - Details on v1 to v2 changes
- **Build Guide**: `BUILD_DEB.md` - Detailed build instructions
- **Migration Summary**: `MIGRATION_SUMMARY.md` - Quick reference

## 🆘 Support

For issues or questions:
- GitHub Issues: https://github.com/aldrineeinsteen/rockpi-penta/issues
- Check logs: `sudo journalctl -u rockpi-penta -f`
- Test manually: `sudo python3 /usr/bin/rockpi-penta/main.py`

## 📄 License

See LICENSE file in repository.
