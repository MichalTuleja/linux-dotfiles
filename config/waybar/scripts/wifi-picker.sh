#!/usr/bin/env bash
set -euo pipefail

# --- Configurable bits ---------------------------------------------------------
WOFI_CONF="${HOME}/.config/wofi/apps.config"
WOFI_STYLE="${HOME}/.config/wofi/dark.css"
PROMPT="Wi-Fi SSID"

# Build a consistent wofi command (use your config/theme if present)
wofi_base=(wofi --show dmenu --prompt "$PROMPT" --insensitive --hide-scroll)
[ -f "$WOFI_CONF" ] && wofi_base+=(--conf "$WOFI_CONF")
[ -f "$WOFI_STYLE" ] && wofi_base+=(--style "$WOFI_STYLE")

# --- Notify we're scanning -----------------------------------------------------
notify-send "Scanning Wi-Fi networks…"

# --- Collect Wi-Fi list --------------------------------------------------------
# nmcli dev wifi rescan >/dev/null 2>&1 || true
# Fields: IN-USE(:* or blank), SSID, SECURITY, SIGNAL
wifi_raw="$(nmcli -t -f IN-USE,SSID,SECURITY,SIGNAL dev wifi list --rescan yes || true)"

if [ -z "${wifi_raw//[[:space:]]/}" ]; then
  printf 'No Wi-Fi networks found.\n' | "${wofi_base[@]}" >/dev/null
  exit 1
fi

# --- Build the menu lines ------------------------------------------------------
# Visible text (for humans) + tab-separated metadata (for parsing).
# We'll make column 2 = SSID, column 3 = SECURITY, column 4 = SIGNAL.
menu_lines=$(
  printf '%s\n' "$wifi_raw" \
  | while IFS=: read -r inuse ssid security signal; do
      # Unescape colons output by nmcli -t
      ssid=${ssid//\\:/:}
      security=${security//\\:/:}

      # Skip empty SSIDs (hidden networks)
      if [ -z "${ssid//[[:space:]]/}" ]; then
        continue
      fi

      # Handle missing security info safely
      if [ -z "${security:-}" ]; then
        security="--"
      fi

      # Icons
      lock=''                               # open by default
      sec_lc="$(printf '%s' "$security" | tr '[:upper:]' '[:lower:]')"
      if [ "$security" != "--" ] && [ "$sec_lc" != "open" ] && [ "$sec_lc" != "none" ]; then
        lock='🔒'
      else
        lock='🌐'
      fi

      wifi_icon=''                         # or use '🛜' for universal emoji
      check=''
      [ "${inuse:-}" = "*" ] && wifi_icon='🟢'

      # Sanitize signal to integer
      signal="${signal%%.*}"
      case "${signal:-0}" in ''|*[!0-9]*) signal=0 ;; esac

      # Visible text + metadata (tab-separated):
      #  col1: pretty text
      #  col2: SSID
      #  col3: SECURITY (may have spaces)
      #  col4: SIGNAL (integer %)
      printf '%s  [%s %s%%]\t%s\t%s\n' \
        "$wifi_icon" "$lock" "$signal" "$ssid" "$check"
    done
)

if [ -z "${menu_lines//[[:space:]]/}" ]; then
  printf 'No visible (broadcast) SSIDs found.\n' | "${wofi_base[@]}" >/dev/null
  exit 1
fi

# --- Show the chooser ----------------------------------------------------------
selected="$(printf '%b' "$menu_lines" | "${wofi_base[@]}")" || exit 1
[ -z "${selected:-}" ] && exit 1

# Extract metadata from tab-separated columns
ssid="$(printf '%s' "$selected" | awk -F'\t' '{print $2}')"
security="$(printf '%s' "$selected" | awk -F'\t' '{print $3}')"

# --- Connect ------------------------------------------------------------------
# If we already have a saved connection for this SSID, bring it up.
if nmcli -t -f NAME connection show | grep -Fxq "$ssid"; then
  nmcli connection up id "$ssid"
  exit 0
fi

# Open vs secured network handling (quote everything!)
sec_lc="$(printf '%s' "$security" | tr '[:upper:]' '[:lower:]')"
if [ -z "${security:-}" ] || [ "$security" = "--" ] || [ "$sec_lc" = "open" ] || [ "$sec_lc" = "none" ]; then
  nmcli dev wifi connect "$ssid"
else
  # Ask NetworkManager for secrets via its agent (safer than plain dmenu input)
  nmcli dev wifi connect "$ssid" --ask
fi
