#!/bin/bash

# # Kill existing bars
# killall -q polybar

# # Wait until dead
# while pgrep -x polybar >/dev/null; do sleep 1; done

# # Launch bar on all monitors
# if type "xrandr" >/dev/null; then
#   for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
#     MONITOR=$m polybar --reload top &
#   done
# else
#   polybar --reload top &
# fi

# Kill any running bar
killall -q polybar

# Wait until it shuts down
while pgrep -x polybar >/dev/null; do sleep 0.5; done

# Launch bar
polybar top &
