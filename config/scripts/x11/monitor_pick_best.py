#!/usr/bin/python3
"""
monitor_pick_best.py
────────────────────
• Pick the largest-pixel-count mode whose HEIGHT is 720-1440 p
• Prefer external HDMI/DP over the built-in eDP/LVDS when pixels tie
• Ignore “scaled” modes on the laptop panel (must be flagged * or +)
• Apply the entire layout with a single xrandr command
• If that command fails, fall back to: eDP-1 --auto, everything else --off
• Console logging only – set MON_PICK_LOGLEVEL=DEBUG for verbose trace
"""

import os
import re
import logging
import subprocess
from pathlib import Path
from shutil import which

# ────────── human-readable limits ──────────
MIN_H = 720
MAX_H = 1440          # never drive >1440 p
ASP_TOL = 0.01        # aspect-ratio slop

# ───────────── logging setup ───────────────
LEVEL = os.getenv("MON_PICK_LOGLEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LEVEL, logging.INFO),
    format="%(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)

# ───────── helper to shell out ─────────────
def run(cmd: str) -> str:
    log.debug("RUN %s", cmd)
    return subprocess.run(
        cmd, shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    ).stdout

# ───────── enumerate every output ──────────
def all_outputs() -> list[str]:
    outs = []
    for ln in run("xrandr --query").splitlines():
        m = re.match(r"^(\S+)\s+(dis)?connected", ln)
        if m:
            outs.append(m.group(1))
    log.debug("Outputs: %s", outs)
    return outs

def connected_outputs() -> list[str]:
    return [o for o in all_outputs()
            if re.search(rf"^{o}\s+connected", run("xrandr --query"), re.M)]

# ───── parse modelines & choose “best” ─────
def parse_modes(output: str, internal: bool) -> list[tuple[int, str]]:
    """Return list of (pixels, 'WxH') modes obeying rules."""
    section = run(f"xrandr --query | sed -n '/^{output} connected/,/^[A-Z]/p'")
    have_native = False
    native_asp = None
    modes = []

    for ln in section.splitlines():
        m = re.match(r"\s+(\d+)x(\d+)", ln)
        if not m:
            continue
        w, h = map(int, m.groups())
        if not (MIN_H <= h <= MAX_H):
            continue
        if internal and not any(ch in ln for ch in "+*"):
            # skip scaled/unsupported modes on eDP/LVDS
            continue
        if not have_native:
            native_asp = w / h
            have_native = True
        if abs((w / h) - native_asp) > ASP_TOL:
            continue
        modes.append((w * h, f"{w}x{h}"))
    log.debug("%s modes: %s", output, modes)
    return modes

def pick_best_monitor() -> tuple[str, str] | None:
    """Return (output, mode) or None."""
    cand = []
    for out in connected_outputs():
        internal = out.lower().startswith(("edp", "lvds"))
        modes = parse_modes(out, internal)
        if modes:
            # largest pixel count
            mode = max(modes, key=lambda t: t[0])[1]
            pixels = max(modes)[0]
            pri = 2 if internal else (1 if out.lower().startswith("dp") else 0)
            cand.append((pixels, pri, out, mode))
    if not cand:
        return None
    pixels, pri, out, mode = sorted(cand, key=lambda t: (-t[0], t[1]))[0]
    log.info("Chosen: %s @ %s  (%d px)", out, mode, pixels)
    return out, mode

# ─────── build & run xrandr command ────────
def build_cmd(primary_out: str, primary_mode: str) -> str:
    parts = []
    for out in all_outputs():
        if out == primary_out:
            parts += ["--output", out, "--mode", primary_mode, "--primary"]
        else:
            parts += ["--output", out, "--off"]
    return "xrandr " + " ".join(parts)

def run_layout(primary_out: str, primary_mode: str) -> bool:
    cmd = build_cmd(primary_out, primary_mode)
    log.info("Applying layout: %s", cmd)
    ok = subprocess.run(cmd, shell=True).returncode == 0
    log.info("→ %s", "success" if ok else "FAILED")
    return ok

# ─────────────── wallpaper ────────────────
def redraw_wallpaper() -> None:
    fp = Path.home() / ".wallpaper"
    if fp.is_file() and which("feh"):
        img = fp.read_text().strip()
        if Path(img).is_file():
            subprocess.run(f'feh --bg-scale "{img}"', shell=True)

# ─────────── polybar helper ────────────
def redraw_polybar() -> None:
    """
    Restart Polybar so it re-reads the new monitor geometry.
    """
    if not which("polybar"):
        log.debug("Polybar not installed – skipping")
        return

    # 1) Gentle restart
    res = subprocess.run("polybar-msg cmd restart",
                         shell=True, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    if res.returncode == 0:
        log.info("Polybar restarted via IPC")
        return

# ─────────────── fallback ──────────────────
def fallback() -> None:
    panel = next((o for o in all_outputs()
                  if o.lower().startswith(("edp", "lvds"))), None)
    cmd = ("xrandr --output {p} --auto --primary ".format(p=panel)
           + " ".join(f"--output {o} --off" for o in all_outputs() if o != panel))
    log.warning("Fallback: %s", cmd)
    subprocess.run(cmd, shell=True)

# ────────────────── main ───────────────────
def main() -> None:
    best = pick_best_monitor()
    if best and run_layout(*best):
        pass
    else:
        log.error("Best layout failed – activating fallback")
        fallback()
    
    redraw_wallpaper()
    redraw_polybar()

if __name__ == "__main__":
    main()
