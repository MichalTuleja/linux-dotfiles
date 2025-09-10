#!/usr/bin/env bash
set -euo pipefail

# --- Dependencies: wofi, pactl (PulseAudio/PipeWire via pactl), notify-send ---

# --- Configurable bits ---------------------------------------------------------
WOFI_CONF="${HOME}/.config/wofi/wifi.config"
WOFI_STYLE="${HOME}/.config/wofi/dark.css"
PROMPT="Audio Output"

# Build a consistent wofi command (use your config/theme if present)
wofi_base=(wofi --show dmenu --prompt "$PROMPT" --insensitive --hide-scroll)
[ -f "$WOFI_CONF" ] && wofi_base+=(--conf "$WOFI_CONF")
[ -f "$WOFI_STYLE" ] && wofi_base+=(--style "$WOFI_STYLE")

# --- Gather sinks --------------------------------------------------------------
sinks_raw="$(pactl list short sinks || true)"
if [ -z "${sinks_raw//[[:space:]]/}" ]; then
  notify-send "No audio sinks found"
  exit 1
fi

# Determine current default sink (by name)
default_sink_name="$(pactl info | awk -F': ' '/Default Sink/ {print $2}')"

# Build "ID<TAB>Label" lines for robust parsing later
sink_list="$(
  printf '%s\n' "$sinks_raw" | awk '{print $1 "\t" $2}' | \
  while IFS=$'\t' read -r id name; do
    # Fetch human-friendly description
    desc="$(
      pactl list sinks | awk -v id="$id" '
        $0 ~ "^Sink #"id"$" {f=1}
        f && /Description:/ {sub(/^[[:space:]]*Description:[[:space:]]*/, "", $0); print; exit}
      '
    )"

    # Optional cleanup to shorten device-heavy descriptions
    desc="$(printf '%s' "$desc" \
      | sed 's/^Tiger Lake-LP Smart Sound Technology Audio Controller *//' \
      | sed 's/.*\(Analog\|HDMI\|Digital\|Line Out\|Bluetooth\)/\1/')"

    desc_lc="$(printf '%s' "$desc" | tr '[:upper:]' '[:lower:]')"

    # Choose an icon
    icon="❓"
    case "$desc_lc" in
      *headphone*) icon="🎧" ;;
      *hdmi*)      icon="📺" ;;
      *bluetooth*) icon="📻" ;;
      *analog*|*line\ out*|*speaker*) icon="🔊" ;;
    esac

    # Mark current default
    mark=""
    if [ "$name" = "$default_sink_name" ]; then
      mark=" 🟢"
    fi

    label="$icon $desc$mark"
    printf '%s\t%s\n' "$id" "$label"
  done
)"

# --- Show chooser (labels only) ------------------------------------------------
selection="$(printf '%s\n' "$sink_list" | cut -f2 | "${wofi_base[@]}")" || exit 1
[ -z "${selection:-}" ] && exit 0

# Map selection back to sink ID (exact match on the label column)
sink_id="$(printf '%s\n' "$sink_list" | awk -v sel="$selection" -F'\t' '$2==sel{print $1; exit}')"
[ -z "${sink_id:-}" ] && exit 1

# Get the sink name too (for robust default-sink set)
sink_name="$(printf '%s\n' "$sinks_raw" | awk -v id="$sink_id" '$1==id{print $2; exit}')"
[ -z "${sink_name:-}" ] && exit 1

# --- Switch default sink and move active streams -------------------------------
pactl set-default-sink "$sink_name"

# Move all active sink-inputs to the new default
while read -r input_id _; do
  [ -n "$input_id" ] && pactl move-sink-input "$input_id" "$sink_name"
done < <(pactl list short sink-inputs)

notify-send "🔊 Switched audio output to: $selection"
