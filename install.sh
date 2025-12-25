#!/bin/bash

# Quick Install Script for rockpi-penta GPIOD v2
# This script builds and installs the DEB package

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║   RockPi Penta Hat - GPIOD v2 Installer ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}Warning: Don't run this script as root!${NC}"
    echo "The script will ask for sudo password when needed."
    exit 1
fi

# Check for dpkg-deb
if ! command -v dpkg-deb &> /dev/null; then
    echo -e "${RED}Error: dpkg-deb not found. Please install dpkg.${NC}"
    exit 1
fi

# Step 1: Build
echo -e "${BLUE}[1/4] Building DEB package...${NC}"
./build-deb.sh

# Step 2: Check GPIOD version
echo ""
echo -e "${BLUE}[2/4] Checking GPIOD version...${NC}"
GPIOD_VERSION=$(python3 -c "import gpiod; print(gpiod.__version__)" 2>/dev/null || echo "not found")

if [ "$GPIOD_VERSION" = "not found" ]; then
    echo -e "${YELLOW}GPIOD not installed. Installing...${NC}"
    sudo apt update
    sudo apt install -y python3-libgpiod
    GPIOD_VERSION=$(python3 -c "import gpiod; print(gpiod.__version__)")
fi

echo "GPIOD Version: $GPIOD_VERSION"

# Check if version is >= 2.0
MAJOR_VERSION=$(echo $GPIOD_VERSION | cut -d. -f1)
if [ "$MAJOR_VERSION" -lt 2 ]; then
    echo -e "${YELLOW}Warning: GPIOD v$GPIOD_VERSION detected. This package requires v2.0+${NC}"
    echo "Attempting to upgrade..."
    sudo apt update
    sudo apt install --only-upgrade python3-libgpiod
fi

# Step 3: Stop existing service if running
echo ""
echo -e "${BLUE}[3/4] Stopping existing service (if any)...${NC}"
if systemctl is-active --quiet rockpi-penta; then
    sudo systemctl stop rockpi-penta
    echo "Existing service stopped."
else
    echo "No existing service running."
fi

# Step 4: Install
echo ""
echo -e "${BLUE}[4/4] Installing package...${NC}"

# Get version from DEBIAN/control
VERSION=$(grep '^Version:' rockpi-penta/DEBIAN/control | awk '{print $2}')
PACKAGE="rockpi-penta_${VERSION}_all.deb"

if [ ! -f "$PACKAGE" ]; then
    echo -e "${RED}Error: Package file not found: $PACKAGE${NC}"
    exit 1
fi

sudo dpkg -i "$PACKAGE"

# Fix any dependency issues
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Fixing dependencies...${NC}"
    sudo apt-get install -f -y
fi

# Wait a moment for service to start
sleep 2

# Check service status
echo ""
echo -e "${BLUE}Checking service status...${NC}"
if systemctl is-active --quiet rockpi-penta; then
    echo -e "${GREEN}✓ Service is running!${NC}"
    sudo systemctl status rockpi-penta --no-pager -l
else
    echo -e "${YELLOW}⚠ Service is not running. Checking logs...${NC}"
    sudo journalctl -u rockpi-penta -n 20 --no-pager
fi

echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║         Installation Complete!           ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

echo "Useful commands:"
echo "  Status:  ${BLUE}sudo systemctl status rockpi-penta${NC}"
echo "  Logs:    ${BLUE}sudo journalctl -u rockpi-penta -f${NC}"
echo "  Restart: ${BLUE}sudo systemctl restart rockpi-penta${NC}"
echo "  Stop:    ${BLUE}sudo systemctl stop rockpi-penta${NC}"
echo ""
echo "Configuration file: ${BLUE}/etc/rockpi-penta.conf${NC}"
echo "Environment file:   ${BLUE}/etc/rockpi-penta.env${NC}"
echo ""
