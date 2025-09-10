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
    current_monitor = None

    for line in output.splitlines():
        if " connected" in line:
            name = line.split()[0]
            current_monitor = name
        elif current_monitor and re.search(r'^\s+\d+x\d+', line):
            parts = line.strip().split()
            res = parts[0]
            freqs = [float(x.replace('*', '').replace('+', '')) for x in parts[1:] if re.match(r'^\d+(\.\d+)?[*+]?$', x)]
            if freqs:
                width, height = map(int, res.split('x'))
                # if height > 720:
                for freq in freqs:
                    # if freq > 49:
                    gcd = math.gcd(width, height)
                    aspect = f"{width // gcd}:{height // gcd}"
                    monitors[current_monitor].append({
                        'res': res,
                        'width': width,
                        'height': height,
                        'freq': freq,
                        'aspect': aspect
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
            label = f"{mon} | {mode['res']} @ {mode['freq']}Hz ({mode['aspect']})"
            sorted_entries.append((label, mon, mode['res'], mode['freq']))
    return sorted_entries

def show_rofi(entries):
    menu = '\n'.join([entry[0] for entry in entries])
    selected = run(f'echo "{menu}" | rofi -dmenu -i -p "Select Monitor Mode"').strip()
    return next((e for e in entries if e[0] == selected), None)

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
