#!/bin/bash

rm -rf ./rockpi-penta/usr/bin/rockpi-penta/__pycache__/
dpkg-deb --build -Z gzip rockpi-penta
