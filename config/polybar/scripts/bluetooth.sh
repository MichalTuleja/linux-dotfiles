#!/usr/bin/env bash
#
# ~/.config/i3blocks/bluetooth.sh
# Dependencies: bluetoothctl, notify-send (optional)

# 1) Is Bluetooth powered on?
if ! bluetoothctl show | grep -q "Powered: yes"; then
    echo " off"
    exit 0
fi

# Function to map major device class to an icon
get_icon_for_class() {
    case "$1" in
        0x00240418*) echo "" ;;   # Audio/Video Headphones
        0x002404*) echo "" ;;   # Audio/Video Portable audio
        0x00250408*) echo "" ;;   # Peripheral Gamepad
        0x000580*) echo "" ;;   # Mouse
        0x00000580*) echo "" ;;   # Mouse
        0x001f00*)  echo "" ;;   # Phone
        0x001c01*)  echo "" ;;   # Computer
        0x*)      echo "" ;;   # Unknown
    esac
}

# 2) Build a list of connected device names + emoji
connected=()
while IFS= read -r line; do
    # Format: "Device MAC Device Name"
    mac=${line#Device }
    mac=${mac%% *}
    name=${line#* $mac }
    info=$(bluetoothctl info "$mac")

    if grep -q "Connected: yes" <<< "$info"; then
        # Extract first word from device name
        short_name=${name%% *}

        # Try to extract Class field (hex code)
        class_hex=$(echo "$info" | awk -F: '/Class:/ {gsub(/ /,"",$2); print $2}')
        icon=$(get_icon_for_class "$class_hex")

        connected+=("$icon")
    fi
done < <(bluetoothctl devices)

# 3) Output for i3blocks
if [ ${#connected[@]} -eq 0 ]; then
    echo ""
else
    IFS=' '; list="${connected[*]}"; unset IFS
    echo " $list"
fi
