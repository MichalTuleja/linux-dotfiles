#!/usr/bin/python3
"""
pick_best_output.py — choose the best output/mode and (optionally) apply it via wlr-randr.

Design goals (plain CLI):
- No GTK or GUI bits.
- No environment guessing/fallbacks: we pass the current os.environ through unchanged.
- If your session/env is correct, this behaves exactly like running wlr-randr in the same shell.

Usage:
  python3 pick_best_output.py           # print decision and command (does NOT apply)
  python3 pick_best_output.py --apply   # apply via wlr-randr and send a notification

Requires:
  - wlr-randr
  - notify-send (optional, for notifications)
"""

import re
import sys
import math
import shlex
import subprocess
import os, glob
from typing import List, Dict, Optional

WLR_RANDR_BIN_PATH = "/usr/bin/wlr-randr"

TARGET_PPI = 109           # desired effective density
SCALE_STEP = 0.125          # round scale to nearest 0.05 (1.00, 1.05, 1.10, ...)

MODE_RE = re.compile(r'^\s{4}(\d+)x(\d+)\s+px,\s+([\d.]+)\s+Hz(?:\s+\((.*?)\))?\s*$')
OUT_RE  = re.compile(r'^(\S+)\s+"([^"]*)"')
MM_RE   = re.compile(r'^\s+Physical size:\s+(\d+)x(\d+)\s+mm')
EN_RE   = re.compile(r'^\s+Enabled:\s+(yes|no)')
MAKE_RE = re.compile(r'^\s+Make:\s+(.*)')
MODEL_RE= re.compile(r'^\s+Model:\s+(.*)')


def passthrough_env() -> dict:
    """Return the current process environment unchanged."""
    return os.environ.copy()


def run_wlr_randr() -> str:
    """
    Invoke wlr-randr and return its stdout. We do not modify the environment:
    if WAYLAND_DISPLAY/XDG_RUNTIME_DIR are wrong or missing, we let it fail.
    """
    env = passthrough_env()
    cp = subprocess.run([WLR_RANDR_BIN_PATH], text=True, capture_output=True, env=env)
    if cp.returncode != 0:
        # Show whatever wlr-randr reported (stderr preferred), along with a few env hints.
        msg = cp.stderr.strip() or cp.stdout.strip() or f"exit {cp.returncode}"
        print(f"Error: failed to run wlr-randr: {msg}", file=sys.stderr)
        print(f"   WAYLAND_DISPLAY={env.get('WAYLAND_DISPLAY')}", file=sys.stderr)
        print(f"   XDG_RUNTIME_DIR={env.get('XDG_RUNTIME_DIR')}", file=sys.stderr)
        print(f"   DBUS_SESSION_BUS_ADDRESS={env.get('DBUS_SESSION_BUS_ADDRESS')}", file=sys.stderr)
        sys.exit(1)
    return cp.stdout


def parse_outputs(text: str) -> List[Dict]:
    outputs: List[Dict] = []
    cur: Optional[Dict] = None
    in_modes = False

    for line in text.splitlines():
        m_out = OUT_RE.match(line)
        if m_out:
            if cur:
                outputs.append(cur)
            cur = {
                "name": m_out.group(1),
                "desc": m_out.group(2),
                "make": None, "model": None,
                "enabled": None,
                "phys_mm": (None, None),
                "modes": []
            }
            in_modes = False
            continue

        if cur is None:
            continue

        if line.strip() == "Modes:":
            in_modes = True
            continue

        if in_modes:
            m_mode = MODE_RE.match(line)
            if m_mode:
                w = int(m_mode.group(1))
                h = int(m_mode.group(2))
                hz_str = m_mode.group(3)
                hz = float(hz_str)
                flags = (m_mode.group(4) or "").lower()
                preferred = "preferred" in flags
                current = "current" in flags
                cur["modes"].append({
                    "w": w, "h": h, "hz": hz, "hz_str": hz_str,
                    "preferred": preferred, "current": current
                })
                continue
            else:
                in_modes = False

        m_mm = MM_RE.match(line)
        if m_mm:
            cur["phys_mm"] = (int(m_mm.group(1)), int(m_mm.group(2)))
            continue

        m_en = EN_RE.match(line)
        if m_en:
            cur["enabled"] = (m_en.group(1) == "yes")
            continue

        m_make = MAKE_RE.match(line)
        if m_make:
            cur["make"] = m_make.group(1).strip()
            continue

        m_model = MODEL_RE.match(line)
        if m_model:
            cur["model"] = m_model.group(1).strip()
            continue

    if cur:
        outputs.append(cur)
    return outputs


def best_mode(modes: List[Dict]) -> Optional[Dict]:
    if not modes:
        return None
    seen = set()
    uniq = []
    for m in modes:
        key = (m["w"], m["h"], round(m["hz"], 6))
        if key not in seen:
            seen.add(key)
            uniq.append(m)
    uniq.sort(key=lambda m: (m["w"]*m["h"], m["preferred"], m["hz"]), reverse=True)
    return uniq[0]


def pick_best_output(outputs: List[Dict]) -> Optional[Dict]:
    candidates = []
    for o in outputs:
        bm = best_mode(o["modes"])
        if not bm:
            continue
        score = (
            o.get("enabled") is True,
            bm["w"] * bm["h"],
            bm["preferred"],
            bm["hz"]
        )
        candidates.append((score, o, bm))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    _score, out, bm = candidates[0]
    out = out.copy()
    out["best_mode"] = bm
    return out


def compute_ppi(w_px: int, h_px: int, mm_w: Optional[int], mm_h: Optional[int]) -> Optional[float]:
    if not mm_w or not mm_h or mm_w <= 0 or mm_h <= 0:
        return None
    diag_px = math.hypot(w_px, h_px)
    diag_in = math.hypot(mm_w, mm_h) / 25.4
    if diag_in <= 0:
        return None
    return diag_px / diag_in


def round_scale(x: float, step: float = SCALE_STEP) -> float:
    return max(1.0, round(x / step) * step)


def build_wlr_randr_cmd(selected: Dict, all_outputs: List[Dict], scale: float) -> List[str]:
    name = selected["name"]
    bm = selected["best_mode"]
    w, h = bm["w"], bm["h"]
    hz = bm["hz_str"]
    args: List[str] = [
        WLR_RANDR_BIN_PATH,
        "--output", name,
        "--on",
        "--mode", f"{w}x{h}@{hz}",
        "--pos", "0,0",
        "--scale", f"{scale:.2f}",
    ]
    for o in all_outputs:
        if o["name"] != name:
            args += ["--output", o["name"], "--off"]
    return args


def notify(msg: str) -> bool:
    """
    Send a desktop notification using `notify-send`.
    Returns True on success, False if notify-send is missing or fails.
    """
    try:
        subprocess.run(["notify-send", msg], check=True, env=passthrough_env())
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def main():
    text = run_wlr_randr()
    outputs = parse_outputs(text)
    if not outputs:
        print("No outputs detected from wlr-randr.", file=sys.stderr)
        sys.exit(2)

    selected = pick_best_output(outputs)
    if not selected:
        print("Could not select a suitable output.", file=sys.stderr)
        sys.exit(3)

    bm = selected["best_mode"]
    mm_w, mm_h = selected.get("phys_mm", (None, None))
    ppi = compute_ppi(bm["w"], bm["h"], mm_w, mm_h)
    if ppi is None:
        scale = 1.0
    else:
        raw_scale = ppi / TARGET_PPI
        scale = round_scale(raw_scale, SCALE_STEP)

    # Example override for a built-in panel; adjust/remove to taste.
    if selected['name'] == "eDP-1":
        scale = 1.125

    cmd = build_wlr_randr_cmd(selected, outputs, scale)

    make = selected.get("make") or ""
    model = selected.get("model") or ""
    message = f"Selected output {selected['name']}\n{make} {model} "
    print(f"# Selected output: {selected['name']}  ({make} {model})")
    print(f"# Best mode: {bm['w']}x{bm['h']} @ {bm['hz_str']} Hz | Enabled now: {selected.get('enabled')}")
    if ppi is not None:
        print(f"# Physical size: {mm_w}x{mm_h} mm  →  PPI ≈ {ppi:.1f}  →  scale ≈ {scale:.2f} (target {TARGET_PPI} PPI)")
    else:
        print(f"# Physical size: unknown  →  default scale = {scale:.2f}")
    print()

    print("# Command (copy-paste to apply):")
    print(shlex.join(cmd))

    if "--apply" in sys.argv:
        print("\n# Applying…")
        try:
            subprocess.run(cmd, check=True, env=passthrough_env())
            notify(message)
        except subprocess.CalledProcessError as e:
            print(f"wlr-randr failed with exit code {e.returncode}", file=sys.stderr)
            sys.exit(e.returncode)
    else:
        notify(f"Test: {message}")


if __name__ == "__main__":
    main()
