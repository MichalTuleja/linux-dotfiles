#!/usr/bin/env bash

# Output the current desktop immediately
wmctrl -d | awk '$2 == "*" { print "" $1 + 1 }'

# Then listen for changes using xprop
xprop -root -spy _NET_CURRENT_DESKTOP | while read -r; do
  wmctrl -d | awk '$2 == "*" { print "" $1 + 1 }'
done
