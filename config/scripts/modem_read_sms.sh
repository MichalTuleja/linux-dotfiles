#!/bin/bash

# Find the first available modem
MODEM_PATH=$(mmcli -L 2>/dev/null | head -n 1 | grep -oE '/org/freedesktop/ModemManager1/Modem/[0-9]+')

if [ -z "$MODEM_PATH" ]; then
    echo "❌ No modem found."
    exit 1
fi

MODEM_ID=$(basename "$MODEM_PATH")

# Get state safely
MODEM_INFO=$(mmcli -m "$MODEM_ID" 2>/dev/null)

echo "📡 Reading SMS from: $MODEM_PATH"
echo

# List and reverse SMS paths
SMS_PATHS=$(mmcli -m "$MODEM_ID" --messaging-list-sms 2>/dev/null | \
    grep -oE '/org/freedesktop/ModemManager1/SMS/[0-9]+' | tac)

if [ -z "$SMS_PATHS" ]; then
    echo "📭 No SMS messages found."
    exit 0
fi

for SMS in $SMS_PATHS; do
    echo "---- $SMS ----"
    mmcli -s "$SMS"
    echo
done
