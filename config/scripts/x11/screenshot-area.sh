#!/bin/bash

filename=~/Screenshots/Screenshot_$(date +%Y%m%d%H%M%S).png

# Use maim with area selection
maim -s "$filename"

# Optional: notify
notify-send "Screenshot saved to $filename"
