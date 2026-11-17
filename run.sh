#!/bin/bash

source venv/bin/activate
export $(cat ./rockpi-penta/usr/bin/rockpi-penta/env/rock_5c_armbian.env | xargs)
python3 ./rockpi-penta/usr/bin/rockpi-penta/main.py
