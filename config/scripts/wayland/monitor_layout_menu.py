#!/usr/bin/env python3
import os
import re
import math
import shlex
import subprocess
from typing import List, Dict, Optional, Tuple

# ------------------ WOFI CONFIG SNIPPET ------------------
WOFI_CONF = os.path.expanduser("~/.config/wofi/wifi.config")
WOFI_STYLE = os.path.expanduser("~/.config/wofi/dark.css")
PROMPT = "🖥 Display Layout"

wofi_base = ["wofi", "--show", "dmenu", "--prompt", PROMPT, "--insensitive", "--hide-scroll"]
if os.path.isfile(WOFI_CONF):
    wofi_base += ["--conf", WOFI_CONF]
if os.path.isfile(WOFI_STYLE):
    wofi_base += ["--style", WOFI_STYLE]

# ------------------ TUNABLES ------------------
TARGET_PPI = 109.0      # desired effective PPI for “Pick best”
SCALE_STEP = 0.125       # round scale (e.g., 1.00, 1.05, 1.10, ...)
INTERNAL_HINTS = ("eDP", "LVDS")  # internal panel name prefixes

# ------------------ UTIL ------------------
def run_out(args: List[str]) -> str:
    """Run a command and return stdout (text), or '' on failure."""
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""

def run_ok(args: List[str]) -> bool:
    try:
        subprocess.run(args, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def notify(summary: str, body: Optional[str] = None):
    exe = shutil_which("notify-send")
    if not exe: return
    cmd = [exe, summary] if not body else [exe, summary, body]
    subprocess.run(cmd, check=False)

def shutil_which(cmd: str) -> Optional[str]:
    from shutil import which
    return which(cmd)

# ------------------ WLR-RANDR PARSE ------------------
MODE_RE = re.compile(r'^\s{4}(\d+)x(\d+)\s+px,\s+([\d.]+)\s+Hz(?:\s+\((.*?)\))?\s*$')
OUT_RE  = re.compile(r'^(\S+)\s+"([^"]*)"')
MM_RE   = re.compile(r'^\s+Physical size:\s+(\d+)x(\d+)\s+mm')
EN_RE   = re.compile(r'^\s+Enabled:\s+(yes|no)')

def get_wlr_info() -> List[Dict]:
    text = run_out(["wlr-randr"])
    if not text:
        return []
    return parse_outputs(text)

def parse_outputs(text: str) -> List[Dict]:
    outputs: List[Dict] = []
    cur: Optional[Dict] = None
    in_modes = False

    for line in text.splitlines():
        m_out = OUT_RE.match(line)
        if m_out:
            if cur: outputs.append(cur)
            cur = {
                "name": m_out.group(1),
                "desc": m_out.group(2),
                "enabled": None,
                "phys_mm": (None, None),
                "modes": [],  # dicts {w,h,hz,hz_str,preferred,current}
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
                w = int(m_mode.group(1)); h = int(m_mode.group(2))
                hz_str = m_mode.group(3)
                hz = float(hz_str)
                flags = (m_mode.group(4) or "").lower()
                cur["modes"].append({
                    "w": w, "h": h, "hz": hz, "hz_str": hz_str,
                    "preferred": "preferred" in flags,
                    "current": "current" in flags
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

    if cur: outputs.append(cur)
    return outputs

def is_internal(name: str) -> bool:
    lname = name.lower()
    return any(lname.startswith(h.lower()) for h in INTERNAL_HINTS)

def find_internal_output(outputs: List[Dict]) -> Optional[Dict]:
    for o in outputs:
        if is_internal(o["name"]):
            return o
    return None

def find_external_output(outputs: List[Dict], internal_name: Optional[str]) -> Optional[Dict]:
    for o in outputs:
        if o["name"] != internal_name:
            return o
    return None

def best_mode(modes: List[Dict]) -> Optional[Dict]:
    if not modes: return None
    # De-duplicate on w,h,hz
    seen = set(); uniq = []
    for m in modes:
        key = (m["w"], m["h"], round(m["hz"], 6))
        if key not in seen:
            seen.add(key); uniq.append(m)
    uniq.sort(key=lambda m: (m["w"]*m["h"], m["preferred"], m["hz"]), reverse=True)
    return uniq[0]

def mode_for_res(modes: List[Dict], w: int, h: int) -> Optional[Dict]:
    candidates = [m for m in modes if m["w"] == w and m["h"] == h]
    if not candidates: return None
    candidates.sort(key=lambda m: m["hz"], reverse=True)
    return candidates[0]

def common_resolutions(a_modes: List[Dict], b_modes: List[Dict]) -> List[Tuple[int,int]]:
    a = {(m["w"], m["h"]) for m in a_modes}
    b = {(m["w"], m["h"]) for m in b_modes}
    res = sorted(list(a & b), key=lambda wh: (wh[0]*wh[1]), reverse=True)
    return res

# ------------------ PPI & SCALE ------------------
def compute_ppi(w_px: int, h_px: int, mm_w: Optional[int], mm_h: Optional[int]) -> Optional[float]:
    if not mm_w or not mm_h or mm_w <= 0 or mm_h <= 0: return None
    diag_px = math.hypot(w_px, h_px)
    diag_in = math.hypot(mm_w, mm_h) / 25.4
    return None if diag_in <= 0 else (diag_px / diag_in)

def round_scale(x: float) -> float:
    return max(1.0, round(x / SCALE_STEP) * SCALE_STEP)

# ------------------ COMMAND BUILDERS ------------------
def cmd_enable_only(name: str, mode: Dict, scale: Optional[float], all_outputs: List[Dict]) -> List[str]:
    args = ["wlr-randr", "--output", name, "--on", "--mode", f"{mode['w']}x{mode['h']}@{mode['hz_str']}", "--pos", "0,0"]
    if scale is not None:
        args += ["--scale", f"{scale:.2f}"]
    for o in all_outputs:
        if o["name"] != name:
            args += ["--output", o["name"], "--off"]
    return args

def cmd_extend_lr(left: Dict, left_mode: Dict, right: Dict, right_mode: Dict) -> List[str]:
    # Left at 0,0; right placed to the right by left_mode width
    args = [
        "wlr-randr",
        "--output", left["name"],  "--on", "--mode", f"{left_mode['w']}x{left_mode['h']}@{left_mode['hz_str']}", "--pos", "0,0",
        "--output", right["name"], "--on", "--mode", f"{right_mode['w']}x{right_mode['h']}@{right_mode['hz_str']}", "--pos", f"{left_mode['w']},0"
    ]
    # Turn off any others (rare)
    # (Assume only two for simplicity; add offs if more present)
    return args

def cmd_mirror(a: Dict, b: Dict, res: Tuple[int,int], a_mode: Dict, b_mode: Dict) -> List[str]:
    # Place both at 0,0 (mirrored)
    w, h = res
    args = [
        "wlr-randr",
        "--output", a["name"], "--on", "--mode", f"{w}x{h}@{a_mode['hz_str']}", "--pos", "0,0",
        "--output", b["name"], "--on", "--mode", f"{w}x{h}@{b_mode['hz_str']}", "--pos", "0,0"
    ]
    return args

# ------------------ ACTIONS ------------------
def external_only(outputs: List[Dict], internal: Optional[Dict]):
    ext = find_external_output(outputs, internal["name"] if internal else None)
    if not ext:
        notify("❌ No external display found"); return
    bm = best_mode(ext["modes"])
    if not bm:
        notify("❌ External has no modes"); return
    cmd = cmd_enable_only(ext["name"], bm, None, outputs)
    subprocess.run(cmd, check=False)

def internal_only(outputs: List[Dict], internal: Optional[Dict]):
    if not internal:
        notify("❌ Internal display not found"); return
    bm = best_mode(internal["modes"])
    if not bm:
        notify("❌ Internal has no modes"); return
    cmd = cmd_enable_only(internal["name"], bm, None, outputs)
    subprocess.run(cmd, check=False)

def extend_to_right(outputs: List[Dict], internal: Optional[Dict]):
    if not internal:
        notify("❌ Internal display not found"); return
    ext = find_external_output(outputs, internal["name"])
    if not ext:
        notify("❌ No external display found"); return
    im = best_mode(internal["modes"]); em = best_mode(ext["modes"])
    if not im or not em:
        notify("❌ Missing modes to extend"); return
    # "Extend to the right" (external on right of internal): internal left, external right
    cmd = cmd_extend_lr(internal, im, ext, em)
    subprocess.run(cmd, check=False)

def extend_to_left(outputs: List[Dict], internal: Optional[Dict]):
    if not internal:
        notify("❌ Internal display not found"); return
    ext = find_external_output(outputs, internal["name"])
    if not ext:
        notify("❌ No external display found"); return
    im = best_mode(internal["modes"]); em = best_mode(ext["modes"])
    if not im or not em:
        notify("❌ Missing modes to extend"); return
    # "Extend to the left" (external on left of internal): external left, internal right
    cmd = cmd_extend_lr(ext, em, internal, im)
    subprocess.run(cmd, check=False)

def mirror_displays(outputs: List[Dict], internal: Optional[Dict]):
    if not internal:
        notify("❌ Internal display not found"); return
    ext = find_external_output(outputs, internal["name"])
    if not ext:
        notify("❌ No external display found"); return
    commons = common_resolutions(internal["modes"], ext["modes"])
    if not commons:
        notify("❌ No common resolution to mirror"); return
    w, h = commons[0]  # highest area
    im = mode_for_res(internal["modes"], w, h)
    em = mode_for_res(ext["modes"], w, h)
    if not im or not em:
        notify("❌ Could not pick mirror modes"); return
    cmd = cmd_mirror(internal, ext, (w, h), im, em)
    subprocess.run(cmd, check=False)

def pick_best(outputs: List[Dict]):
    """
    Choose output by: enabled first, then largest pixel area, preferred flag, highest Hz.
    Set scale targeting ~109 PPI and switch ALL others off.
    """
    candidates = []
    for o in outputs:
        bm = best_mode(o["modes"])
        if not bm: continue
        score = (o.get("enabled") is True, bm["w"]*bm["h"], bm["preferred"], bm["hz"])
        candidates.append((score, o, bm))
    if not candidates:
        notify("❌ No outputs with modes found"); return
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, out, bm = candidates[0]

    mm_w, mm_h = out.get("phys_mm", (None, None))
    ppi = compute_ppi(bm["w"], bm["h"], mm_w, mm_h)
    scale = None
    if ppi is not None:
        raw = ppi / TARGET_PPI
        scale = round_scale(raw)

    cmd = cmd_enable_only(out["name"], bm, scale, outputs)
    subprocess.run(cmd, check=False)
    s = f"{out['name']} {bm['w']}x{bm['h']}@{bm['hz_str']}  scale={scale:.2f}" if scale else f"{out['name']} {bm['w']}x{bm['h']}@{bm['hz_str']}"
    notify("✅ Picked best output", s)

# ------------------ MENU ------------------
def wofi_select(options: List[str]) -> Optional[str]:
    """Show a Wofi dmenu and return the selected option, or None."""
    data = "\n".join(options)
    try:
        p = subprocess.run(wofi_base, input=data, text=True, capture_output=True, check=False)
        choice = p.stdout.strip()
        return choice if choice in options else None
    except Exception:
        return None

def main():
    options = [
        "Pick best",
        "External only",
        "Mirror display",
        "Extend to the right",
        "Extend to the left",
        "Internal only"
    ]
    choice = wofi_select(options)
    if not choice:
        return

    outputs = get_wlr_info()
    if not outputs:
        notify("❌ wlr-randr returned no outputs")
        return

    internal = find_internal_output(outputs)

    if choice == "External only":
        external_only(outputs, internal)
    elif choice == "Mirror display":
        mirror_displays(outputs, internal)
    elif choice == "Extend to the right":
        extend_to_right(outputs, internal)
    elif choice == "Extend to the left":
        extend_to_left(outputs, internal)
    elif choice == "Internal only":
        internal_only(outputs, internal)
    elif choice == "Pick best":
        pick_best(outputs)

if __name__ == "__main__":
    main()
