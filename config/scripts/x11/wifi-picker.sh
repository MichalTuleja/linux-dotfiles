#!/bin/bash

echo "Scanning Wi-Fi networks..." | rofi -dmenu -p "Wi-Fi SSID" -lines 1 rofi -config ~/.config/rofi/wifi.rasi &
pid=$!

# Wait while nmcli scans
# Use terse output for reliable parsing: IN-USE, SSID, SECURITY, SIGNAL
choices=$(nmcli -t -f IN-USE,SSID,SECURITY,SIGNAL dev wifi list --rescan yes || true)
kill "$pid" 2>/dev/null

# Process and add icons + tab-separated metadata
formatted_choices=$(printf '%s\n' "$choices" | while IFS=: read -r inuse ssid security signal; do
    # Unescape colons output by nmcli -t
    ssid=${ssid//\\:/:}
    security=${security//\\:/:}

    # Skip empty SSIDs (hidden networks)
    if [ -z "${ssid//[[:space:]]/}" ]; then
        continue
    fi

    # Handle missing security info safely
    if [ -z "${security:-}" ]; then security="--"; fi

    # Icons
    lock='' # open by default
    sec_lc="$(printf '%s' "$security" | tr '[:upper:]' '[:lower:]')"
    if [ "$security" != "--" ] && [ "$sec_lc" != "open" ] && [ "$sec_lc" != "none" ]; then
        lock='🔒'
    else
        lock='🌐'
    fi

    wifi_icon='' # or use '🛜' for universal emoji
    check=''
    [ "${inuse:-}" = "*" ] && wifi_icon='🟢'

    # Sanitize signal to integer
    signal="${signal%%.*}"
    case "${signal:-0}" in ''|*[!0-9]*) signal=0 ;; esac

    # Visible text + metadata (tab-separated):
    # col1: pretty text
    # col2: SSID
    # col3: SECURITY (may have spaces)
    # col4: SIGNAL (integer %)
    printf '%s [%s %s%%]\t%s\t%s\n' \
        "$wifi_icon" "$lock" "$signal" "$ssid" "$check"
done)

# Show menu with icons
selected=$(echo "$formatted_choices" | rofi -dmenu \
  -p "Wi-Fi SSID" \
  -config ~/.config/rofi/wifi.rasi)

# Extract SSID from tab-separated metadata (column 2)
ssid=$(printf '%s' "$selected" | awk -F '\t' '{print $2}')

# Connect
[ -n "$ssid" ] && nmcli dev wifi connect "$ssid"
