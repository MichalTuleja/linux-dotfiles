#!/bin/bash

# Handle mouse click (left = 1)
if [ "$BLOCK_BUTTON" = "1" ]; then
    #nm-connection-editor &
    #alacritty -e /bin/bash -c ".config/i3/scripts/modem_read_sms.sh | less"
    ~/.config/scripts/x11/modem_read_sms_zenity.py
fi

if [ "$BLOCK_BUTTON" = "3" ]; then
    nm-connection-editor &
fi

# Find the first modem path from mmcli -L
modem_path=$(mmcli -L 2>/dev/null | head -n 1 | awk '{print $1}')
modem_id=$(basename "$modem_path")

# # Only proceed if a modem is found
# if [ -n "$modem_id" ]; then
#     signal=$(mmcli -m "$modem_id" 2>/dev/null | awk -F: '/signal quality/ {gsub(/[^0-9]/,"",$2); print $2}')

#     if [ -n "$signal" ]; then
#         echo "📶 LTE (${signal}%)"
#     else
#         echo "📶 LTE: N/A"
#     fi
# else
#     echo "📶 LTE: No modem"
# fi

# Only proceed if a modem is found
if [ -n "$modem_id" ]; then
    signal=$(mmcli -m "$modem_id" 2>/dev/null | awk -F: '/signal quality/ {gsub(/[^0-9]/,"",$2); print $2}')

    if [ -n "$signal" ]; then
        echo " LTE (${signal}%)"
    else
        echo " N/A"
    fi
else
    echo " No modem"
fi
