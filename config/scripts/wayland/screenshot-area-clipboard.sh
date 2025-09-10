#!/bin/bash

filename=~/Screenshots/Screenshot_$(date +%Y%m%d%H%M%S).png
grim -g "$(slurp)" - | wl-copy
notify-send "Screenshot saved to $filename"
