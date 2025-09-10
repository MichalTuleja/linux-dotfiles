#!/bin/bash

current_layout=$(setxkbmap -query | awk '/layout:/ { print $2 }')
current_variant=$(setxkbmap -query | awk '/variant:/ { print $2 }')

if [ "$current_layout" == "us" ]; then
    setxkbmap pl
else
    setxkbmap us -variant altgr-intl
fi
