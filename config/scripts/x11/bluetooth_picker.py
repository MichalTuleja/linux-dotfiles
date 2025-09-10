#!/usr/bin/env python3

import subprocess
import os
import re
from typing import List, Tuple


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def get_paired_devices() -> List[Tuple[str, str]]:
    """Return list of (mac, name) for paired devices."""
    # Try modern form first
    p = run_cmd(["bluetoothctl", "devices", "Paired"])
    out = p.stdout.strip()
    if p.returncode != 0 or not out:
        # Fallback to older alias
        p = run_cmd(["bluetoothctl", "paired-devices"])
        out = p.stdout.strip()
    devices: List[Tuple[str, str]] = []
    for line in out.splitlines():
        # Lines look like: "Device AA:BB:CC:DD:EE:FF Device Name With Spaces"
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) >= 3 and parts[0] == "Device":
            mac, name = parts[1], parts[2]
            devices.append((mac, name))
    return devices


def parse_icon_symbol(name: str, icon_hint: str, info_text: str) -> str:
    """Map bluetoothctl icon/name/uuids to a device emoji."""
    name_lc = (name or "").lower()
    icon_lc = (icon_hint or "").lower()
    info_lc = (info_text or "").lower()

    def has_any(s: str, words) -> bool:
        return any(w in s for w in words)

    # Prefer explicit icon hints
    if has_any(icon_lc, ["headphone", "headset", "earbud", "audio-headset", "audio-headphones"]):
        return ""  # fa-headphones
    if has_any(icon_lc, ["speaker", "audio-speakers", "audio-card"]):
        return ""  # fa-volume-high
    if has_any(icon_lc, ["keyboard"]):
        return ""  # fa-keyboard
    if has_any(icon_lc, ["mouse"]):
        return ""  # fa-mouse
    if has_any(icon_lc, ["gamepad", "joystick", "controller"]):
        return ""  # fa-gamepad
    if has_any(icon_lc, ["phone", "smartphone", "mobile"]):
        return ""  # fa-mobile
    if has_any(icon_lc, ["computer", "laptop", "desktop"]):
        return ""  # fa-laptop
    if has_any(icon_lc, ["car"]):
        return ""  # fa-car
    if has_any(icon_lc, ["tv", "display", "video-display"]):
        return ""  # fa-television
    if has_any(icon_lc, ["printer"]):
        return ""  # fa-print
    if has_any(icon_lc, ["network", "modem", "net", "panu", "nap"]):
        return ""  # fa-network-wired

    # Heuristics by name
    if has_any(name_lc, ["buds", "headphone", "headset", "airpods", "earbud"]):
        return ""
    if "keyboard" in name_lc:
        return ""
    if "mouse" in name_lc:
        return ""
    if "speaker" in name_lc:
        return ""
    if has_any(name_lc, ["gamepad", "controller"]):
        return ""
    if has_any(name_lc, ["car", "handsfree"]):
        return ""
    if has_any(name_lc, ["tv"]):
        return ""
    if has_any(name_lc, ["phone", "iphone", "android", "pixel", "galaxy"]):
        return ""

    # Heuristics by UUID presence
    if has_any(info_lc, ["audio sink", "a2dp sink", "headset", "handsfree", "avrcp"]):
        return ""
    if has_any(info_lc, ["hid", "hogp"]):
        return ""
    if has_any(info_lc, ["panu", "nap"]):
        return ""

    # Fallback generic device
    return ""  # fa-bluetooth


def clean_name(name: str) -> str:
    """Remove any UUID-like sequences from a name as a safeguard."""
    # Remove 128-bit UUIDs like 0000110b-0000-1000-8000-00805f9b34fb
    name = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "", name)
    # Remove 16-bit UUIDs in parentheses, e.g., (110B)
    name = re.sub(r"\([0-9a-fA-F]{4}\)", "", name)
    # Collapse extra spaces
    return re.sub(r"\s+", " ", name).strip()


def get_device_metadata(mac: str, fallback_name: str) -> tuple[bool, str, str]:
    """Return (connected, symbol, alias) for device by mac."""
    p = run_cmd(["bluetoothctl", "info", mac])
    connected = False
    icon_hint = ""
    alias = fallback_name
    if p.returncode == 0:
        for line in p.stdout.splitlines():
            ls = line.strip()
            if ls.lower().startswith("connected:"):
                connected = ls.split(":", 1)[1].strip().lower().startswith("yes")
            elif ls.lower().startswith("icon:"):
                icon_hint = ls.split(":", 1)[1].strip()
            elif ls.lower().startswith("alias:"):
                alias = ls.split(":", 1)[1].strip()
    alias = clean_name(alias)
    symbol = parse_icon_symbol(alias, icon_hint, p.stdout if p.returncode == 0 else "")
    return connected, symbol, alias


def show_rofi(choices: List[Tuple[str, str, bool, str]]) -> str:
    """Show rofi with pretty choices; return selected MAC or empty string."""
    # Format: visible text + tab + MAC to extract later
    lines = []
    for mac, alias, connected, symbol in choices:
        suffix = " 🟢" if connected else ""
        pretty = f"{symbol} {alias}{suffix}"
        lines.append(f"{pretty}\t{mac}")

    rofi_cfg = os.path.expanduser("~/.config/rofi/wifi.rasi")
    rofi_cmd = [
        "rofi",
        "-dmenu",
        "-p",
        " Bluetooth",
        "-config",
        rofi_cfg,
    ]

    # Invoke rofi
    p = subprocess.run(
        rofi_cmd,
        input="\n".join(lines) + ("\n" if lines else ""),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    selected = p.stdout.strip()
    if not selected:
        return ""
    # Extract MAC from tab-separated column 2
    mac = selected.split("\t")[1].strip() if "\t" in selected else ""
    return mac


def main() -> int:
    devices = get_paired_devices()
    if not devices:
        # No paired devices
        subprocess.run(
            ["rofi", "-e", "No paired Bluetooth devices found."]
        )
        return 0

    # Query connection status and symbol (best-effort)
    choices: List[Tuple[str, str, bool, str]] = []
    for mac, name in devices:
        connected, symbol, alias = get_device_metadata(mac, name)
        choices.append((mac, alias, connected, symbol))

    mac = show_rofi(choices)
    if not mac:
        return 0

    # Attempt to connect
    connect = run_cmd(["bluetoothctl", "connect", mac])
    if connect.returncode == 0:
        return 0

    # If connect failed, show brief error
    msg = connect.stderr.strip() or connect.stdout.strip() or "Failed to connect"
    # Keep it short for rofi -e
    msg = (msg[:200] + "…") if len(msg) > 200 else msg
    subprocess.run(["rofi", "-e", f"Bluetooth: {msg}"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
