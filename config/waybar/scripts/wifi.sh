#!/bin/bash

# Get the first wireless interface, if any
iface=$(iw dev | awk '$1=="Interface"{print $2}' | head -n1)

# No interface found
if [ -z "$iface" ]; then
    echo " N/A"
    exit 1
fi

# Check if interface is UP
if ! ip link show "$iface" | grep -q "state UP"; then
    echo " Disabled"
    exit 0
fi

# Get connection status
link_info=$(iw dev "$iface" link)

# Not connected to any network
if echo "$link_info" | grep -q "Not connected."; then
    echo " Disconnected"
    exit 0
fi

# Parse SSID and signal strength
ssid=$(awk -F ': ' '/SSID:/ {print $2}' <<< "$link_info")
signal_dbm=$(awk '/signal:/ {print $2}' <<< "$link_info")

# Sanity check
[ -z "$signal_dbm" ] && echo " $ssid" && exit 0

# Clamp dBm to -100 to -50 range
if [ "$signal_dbm" -le -100 ]; then
    percent=0
elif [ "$signal_dbm" -ge -50 ]; then
    percent=100
else
    percent=$((2 * (signal_dbm + 100)))
fi

echo " $ssid (${percent}%)"
