#!/bin/bash

filename=~/Screenshots/Screenshot_$(date +%Y%m%d%H%M%S).png
grim -g "$(slurp)" "$filename"

# TODO: Notify only if exit with zero
notify-send "Screenshot saved to $filename"
