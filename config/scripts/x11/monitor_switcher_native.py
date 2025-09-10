#!/usr/bin/env python3

import subprocess
import re
import os

def redraw_wallpaper():
    wallpaper_file = os.path.expanduser("~/.wallpaper")
    if os.path.isfile(wallpaper_file):
        with open(wallpaper_file) as f:
            image_path = f.read().strip()
            if os.path.isfile(image_path):
                subprocess.run(f'feh --bg-scale "{image_path}"', shell=True)

def run(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip()

def parse_native_modes():
    output = run("xrandr")
    monitors = {}
    lines = output.splitlines()

    current_monitor = None
    found_native = False

    for line in lines:
        if " connected" in line:
            current_monitor = line.split()[0]
            monitors[current_monitor] = {"res": None, "freqs": []}
            found_native = False
            continue

        if current_monitor and re.match(r'^\s+\d+x\d+', line):
            if not found_native:
                # First resolution listed → native
                res_match = re.match(r'^\s+(\d+x\d+)', line)
                freq_matches = re.findall(r'(\d+\.\d+)\*?\+?', line)

                if res_match and freq_matches:
                    res = res_match.group(1)
                    freqs = [float(f) for f in freq_matches]
                    monitors[current_monitor]['res'] = res
                    monitors[current_monitor]['freqs'] = freqs
                    found_native = True

    # Select max refresh for native resolution
    final_monitors = {}
    for mon, info in monitors.items():
        if info['res'] and info['freqs']:
            final_monitors[mon] = {
                'res': info['res'],
                'freq': max(info['freqs'])
            }

    return final_monitors

def show_rofi(monitors):
    entries = []
    for mon, info in monitors.items():
        label = f"{mon} | {info['res']} @ {info['freq']}Hz"
        entries.append((label, mon, info['res'], info['freq']))

    # Sort alphabetically, eDP last, HDMI before DP
    def sort_key(entry):
        name = entry[1].lower()
        if name.startswith('edp'):
            return (2, name)
        elif name.startswith('hdmi'):
            return (0, name)
        elif name.startswith('dp'):
            return (1, name)
        return (3, name)

    entries.sort(key=sort_key)
    menu = '\n'.join(e[0] for e in entries)
    selected = run(f'echo "{menu}" | rofi -dmenu -i -p "🖥 Native Display Setup"')

    return next((e for e in entries if e[0] == selected), None)

def apply_mode(monitor, res, freq):
    all_monitors = run("xrandr --listmonitors").splitlines()[1:]
    all_outputs = [line.strip().split()[-1] for line in all_monitors]

    for out in all_outputs:
        subprocess.run(f"xrandr --output {out} --off", shell=True)

    subprocess.run(f"xrandr --output {monitor} --mode {res} --rate {freq} --primary", shell=True)

def main():
    monitors = parse_native_modes()
    if not monitors:
        subprocess.run(['notify-send', '❌ No connected displays found'])
        return

    selected = show_rofi(monitors)
    if selected:
        _, monitor, res, freq = selected
        apply_mode(monitor, res, freq)
        redraw_wallpaper()

if __name__ == "__main__":
    main()
