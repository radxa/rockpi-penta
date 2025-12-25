# Building and Installing the DEB Package

## Quick Build & Install

### 1. Build the DEB package
```bash
# Navigate to the project directory
cd ~/rockpi-penta

# Build the package
./build-deb.sh
```

### 2. Install the DEB package
```bash
# Install the generated .deb file
sudo dpkg -i rockpi-penta_0.3_all.deb

# If there are dependency issues, fix them with:
sudo apt-get install -f
```

### 3. Check Service Status
```bash
# Check if service is running
sudo systemctl status rockpi-penta

# View logs
sudo journalctl -u rockpi-penta -f

# Stop/Start/Restart service
sudo systemctl stop rockpi-penta
sudo systemctl start rockpi-penta
sudo systemctl restart rockpi-penta
```

## Manual Build Process

If you prefer to build manually:

```bash
# 1. Ensure correct permissions
chmod +x rockpi-penta/DEBIAN/postinst
chmod +x rockpi-penta/DEBIAN/prerm

# 2. Build the package
dpkg-deb --build rockpi-penta

# 3. This creates: rockpi-penta.deb
# Optionally rename it:
mv rockpi-penta.deb rockpi-penta_0.3_all.deb
```

## Package Contents

The DEB package includes:
- **Python scripts**: `/usr/bin/rockpi-penta/*.py`
- **Service file**: `/lib/systemd/system/rockpi-penta.service`
- **Configuration**: `/etc/rockpi-penta.conf`
- **Environment files**: `/usr/bin/rockpi-penta/env/*.env`
- **Fonts**: `/usr/bin/rockpi-penta/fonts/`
- **Overlays**: `/usr/bin/rockpi-penta/overlays/`

## Post-Installation

The postinst script automatically:
1. Installs Python dependencies (`adafruit-circuitpython-ssd1306`)
2. Detects your board model
3. Configures appropriate environment variables
4. Enables and starts the systemd service
5. Configures device tree overlays if needed

## Uninstallation

```bash
sudo apt remove rockpi-penta
# or
sudo dpkg -r rockpi-penta
```

## Troubleshooting

### Service fails to start
```bash
# Check logs
sudo journalctl -u rockpi-penta -n 50

# Check environment variables
cat /etc/rockpi-penta.env

# Test manually
sudo --preserve-env=OLED_RESET,HARDWARE_PWM,SDA,SCL,BUTTON_CHIP,BUTTON_LINE,FAN_CHIP,FAN_LINE \
  python3 /usr/bin/rockpi-penta/main.py
```

### GPIOD version check
```bash
# Verify GPIOD v2 is installed
python3 -c "import gpiod; print(gpiod.__version__)"

# Should show version >= 2.0
```

### Update libgpiod if needed
```bash
sudo apt update
sudo apt install python3-libgpiod
```

## Development Testing

To test without installing the DEB:
```bash
cd rockpi-penta/usr/bin/rockpi-penta

# Set environment for your board (example for Rock Pi 4)
export HARDWARE_PWM=1
export PWMCHIP=pwmchip0
export FAN_CHIP=0
export FAN_LINE=150
export BUTTON_CHIP=0
export BUTTON_LINE=154
export OLED_RESET=GPIO13
export SCL=SCL1
export SDA=SDA1

# Run manually
python3 main.py
```

## Releasing

After building the DEB:
1. Test installation on target hardware
2. Tag the release in git
3. Upload the .deb to GitHub releases or your repository

```bash
# Tag the release
git tag -a v0.3-gpiod-v2 -m "GPIOD v2 release"
git push origin v0.3-gpiod-v2

# Create GitHub release and attach rockpi-penta_0.3_all.deb
```
