#!/usr/bin/env python3

import subprocess
import re
from collections import defaultdict
import os
import math

def redraw_wallpaper():
    wallpaper_file = os.path.expanduser("~/.wallpaper")
    if os.path.isfile(wallpaper_file):
        with open(wallpaper_file) as f:
            image_path = f.read().strip()
            if os.path.isfile(image_path):
                subprocess.run(f'feh --bg-scale "{image_path}"', shell=True)

def run(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout

def get_monitors():
    output = run("xrandr")
    monitors = defaultdict(list)
    native_aspect = {}
    native_resolutions = {}
    native_freqs = {}
    current_monitor = None
    seen_first_mode = {}

    for line in output.splitlines():
        if " connected" in line:
            current_monitor = line.split()[0]
            native_aspect[current_monitor] = None
            native_resolutions[current_monitor] = None
            native_freqs[current_monitor] = 0.0
            seen_first_mode[current_monitor] = False
        elif current_monitor and re.match(r'^\s+\d+x\d+', line):
            parts = line.strip().split()
            res = parts[0]
            width, height = map(int, res.split('x'))
            freqs_raw = parts[1:]

            if not (720 <= height <= 1440):
                continue

            gcd = math.gcd(width, height)
            aspect = f"{width // gcd}:{height // gcd}"

            is_native = any('*' in f for f in freqs_raw)
            if not is_native and not seen_first_mode[current_monitor]:
                is_native = True
                seen_first_mode[current_monitor] = True

            # Save native resolution and aspect
            if is_native and native_aspect[current_monitor] is None:
                native_aspect[current_monitor] = aspect
                native_resolutions[current_monitor] = res

            # Compare aspect ratio to native (with tolerance)
            if native_aspect[current_monitor] is not None:
                native_ratio = eval(native_aspect[current_monitor].replace(":", "/"))
                current_ratio = width / height
                if abs(current_ratio - native_ratio) > 0.01:
                    continue

            for f in freqs_raw:
                match = re.match(r'^(\d+(?:\.\d+)?)([*+]?)$', f)
                if match:
                    freq = float(match.group(1))
                    if freq > 49:
                        is_best_native = (
                            res == native_resolutions[current_monitor] and freq > native_freqs[current_monitor]
                        )
                        if is_best_native:
                            native_freqs[current_monitor] = freq
                        monitors[current_monitor].append({
                            'res': res,
                            'width': width,
                            'height': height,
                            'freq': freq,
                            'aspect': aspect,
                            'is_best_native': is_best_native
                        })

    return monitors

def sort_monitors(monitors):
    def monitor_sort_key(name):
        if name.lower().startswith("edp"):
            return (2, name)
        elif name.lower().startswith("hdmi"):
            return (1, name)
        elif name.lower().startswith("dp"):
            return (0, name)
        else:
            return (3, name)

    sorted_entries = []
    for mon in sorted(monitors.keys(), key=monitor_sort_key):
        for mode in sorted(monitors[mon], key=lambda x: (-x['height'], -x['freq'])):
            label_text = f"{mon} | {mode['res']} @ {mode['freq']}Hz ({mode['aspect']})"
            if mode.get('is_best_native'):
                label = f"<b>{label_text}</b>"
            else:
                label = label_text
            sorted_entries.append((label, mon, mode['res'], mode['freq']))
    return sorted_entries

def show_rofi(entries):
    menu = '\n'.join([entry[0] for entry in entries])
    selected = run(f'echo "{menu}" | rofi -dmenu -markup-rows -p "Select Monitor Mode"').strip()
    # Strip Pango tags before matching
    plain_entries = {re.sub(r'<[^>]+>', '', e[0]): e for e in entries}
    return plain_entries.get(re.sub(r'<[^>]+>', '', selected), None)

def apply_mode(monitor, res, freq):
    all_monitors = run("xrandr --listmonitors").splitlines()[1:]
    all_names = [line.strip().split()[-1] for line in all_monitors]

    for mon in all_names:
        subprocess.run(f"xrandr --output {mon} --off", shell=True)

    cmd = f"xrandr --output {monitor} --mode {res} --rate {freq} --primary"
    subprocess.run(cmd, shell=True)

def main():
    monitors = get_monitors()
    if not monitors:
        subprocess.run(['notify-send', '❌ No displays or resolutions found'])
        return

    entries = sort_monitors(monitors)
    selection = show_rofi(entries)

    if selection:
        _, monitor, res, freq = selection
        apply_mode(monitor, res, freq)
        redraw_wallpaper()

if __name__ == "__main__":
    main()
