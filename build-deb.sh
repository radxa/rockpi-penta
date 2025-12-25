#!/bin/bash
set -e

# Build script for rockpi-penta DEB package
# Version is automatically extracted from DEBIAN/control

echo "=========================================="
echo "Building rockpi-penta DEB package"
echo "GPIOD v2 Migration"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in the correct directory
if [ ! -d "rockpi-penta" ]; then
    echo -e "${RED}Error: rockpi-penta directory not found!${NC}"
    echo "Please run this script from the repository root."
    exit 1
fi

# Get version from DEBIAN/control
VERSION=$(grep '^Version:' rockpi-penta/DEBIAN/control | awk '{print $2}')
if [ -z "$VERSION" ]; then
    echo -e "${RED}Error: Could not extract version from DEBIAN/control${NC}"
    exit 1
fi

echo -e "${BLUE}Package version: ${VERSION}${NC}"

# Set correct permissions for DEBIAN scripts
echo -e "${BLUE}Setting correct permissions...${NC}"
chmod 755 rockpi-penta/DEBIAN/postinst
chmod 755 rockpi-penta/DEBIAN/prerm

# Ensure Python scripts are executable
chmod +x rockpi-penta/usr/bin/rockpi-penta/*.py

# Build the package
echo -e "${BLUE}Building DEB package...${NC}"
dpkg-deb --build rockpi-penta

# Rename to include version
PACKAGE_NAME="rockpi-penta_${VERSION}_all.deb"
if [ -f "rockpi-penta.deb" ]; then
    mv rockpi-penta.deb "$PACKAGE_NAME"
    echo -e "${GREEN}✓ Package built successfully: ${PACKAGE_NAME}${NC}"
else
    echo -e "${RED}Error: Package build failed!${NC}"
    exit 1
fi

# Display package info
echo ""
echo -e "${BLUE}Package Information:${NC}"
dpkg-deb --info "$PACKAGE_NAME"

echo ""
echo -e "${BLUE}Package Contents:${NC}"
dpkg-deb --contents "$PACKAGE_NAME" | head -20
echo "... (showing first 20 files)"

# Calculate package size
SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)
echo ""
echo -e "${GREEN}=========================================="
echo "Build Complete!"
echo "=========================================="
echo "Package: ${PACKAGE_NAME}"
echo "Size: ${SIZE}"
echo ""
echo "To install:"
echo "  sudo dpkg -i ${PACKAGE_NAME}"
echo ""
echo "To fix dependencies (if needed):"
echo "  sudo apt-get install -f"
echo -e "${NC}"
