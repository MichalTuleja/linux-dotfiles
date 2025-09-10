#!/bin/bash

# Dependencies: rofi, pactl (PulseAudio or PipeWire via pactl)

# Get list of sink IDs and names
sinks=$(pactl list short sinks | awk '{print $1 "|" $2}')

if [ -z "$sinks" ]; then
    notify-send "No audio sinks found"
    exit 1
fi

sink_list=$(echo "$sinks" | while IFS="|" read -r id name; do
    # Get description
    desc=$(pactl list sinks | grep -A 20 "Sink #$id" | grep "Description:" | head -n1 | cut -d: -f2- | sed 's/^ *//' \
      | sed 's/^Tiger Lake-LP Smart Sound Technology Audio Controller *//' \
      | sed 's/.*\(Analog\|HDMI\|Digital\|Line Out\|Bluetooth\)/\1/')

    # Normalize for matching
    desc_lc=$(echo "$desc" | tr '[:upper:]' '[:lower:]')

    # Choose icon
    case "$desc_lc" in
    *headphone*)
        icon="🎧"
        ;;
    *hdmi*)
        icon="📺"
        ;;
    *bluetooth*)
        icon="📻"
        ;;
    *analog*)
        icon="🔊"
        ;;
    *line\ out*)
        icon="🔊"
        ;;
    *speaker*)
        icon="🔊"
        ;;
    *)
        icon="❓"
        ;;
    esac


    # Print for rofi
    echo "$id|$icon $desc"
done)

# Show rofi menu
selection=$(echo "$sink_list" | cut -d'|' -f2 | rofi -dmenu -p "Select Audio Output")

# Exit if user cancelled
[ -z "$selection" ] && exit 0

# Extract selected sink ID
sink_id=$(echo "$sink_list" | grep "|$selection" | cut -d'|' -f1)

# Set default sink
pactl set-default-sink "$sink_id"

# Move all active streams to new sink
for input in $(pactl list short sink-inputs | awk '{print $1}'); do
    pactl move-sink-input "$input" "$sink_id"
done

notify-send "🔊 Switched audio output to: $selection"
