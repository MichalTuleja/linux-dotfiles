#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wlr_outputs.py — manage Wayland outputs via wlr-output-management-unstable-v1

List heads and apply atomic changes (mode/scale/pos/transform/enable/disable).
Tested with the python-wayland library (module name: 'wayland').

Usage examples:
  # List current heads/modes
  python wlr_outputs.py list

  # Set an exact mode by size + refresh (Hz), and scale/pos/transform
  python wlr_outputs.py set --head DP-1 --mode 2560x1440@144 --scale 1.25 --pos 0,0 --transform normal

  # Pick preferred refresh for a size (no @refresh) and enable head
  python wlr_outputs.py set --head HDMI-A-1 --mode 1920x1080 --enable

  # Disable a head
  python wlr_outputs.py set --head eDP-1 --disable

  # Dry-run without applying
  python wlr_outputs.py set --head DP-1 --mode 3440x1440@120 --test

Notes:
- Refresh units in protocol are mHz; we accept Hz and convert.
- The protocol requires ALL heads be configured in a request – we take care of that.
- If a compositor rounds scale (no fractional support), that’s expected.

"""
import argparse
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    import wayland
    from wayland.client import wayland_class
except Exception as e:
    print("This script requires the 'python-wayland' package (module 'wayland').\n"
          "Install it with: pip install python-wayland\n\n"
          f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

# ----- Helpers ----------------------------------------------------------------

TRANSFORM_STR_TO_ENUM = {
    "normal": 0,
    "90": 1, "rot90": 1, "90deg": 1,
    "180": 2, "rot180": 2, "180deg": 2,
    "270": 3, "rot270": 3, "270deg": 3,
    "flipped": 4,
    "flipped-90": 5, "flip-90": 5,
    "flipped-180": 6, "flip-180": 6,
    "flipped-270": 7, "flip-270": 7,
}

def parse_mode_str(s: str) -> Tuple[int, int, Optional[int]]:
    """
    Parse strings like '1920x1080', '1920x1080@60', '2560x1440@143.9'
    Returns (w, h, refresh_mHz or None)
    """
    m = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)(?:\s*@\s*([\d.]+))?\s*", s)
    if not m:
        raise ValueError(f"Invalid mode string: {s!r}")
    w, h = int(m.group(1)), int(m.group(2))
    r_hz = m.group(3)
    r_mhz = int(round(float(r_hz) * 1000)) if r_hz else None
    return w, h, r_mhz

def parse_pos_str(s: str) -> Tuple[int, int]:
    m = re.fullmatch(r"\s*(-?\d+)\s*,\s*(-?\d+)\s*", s)
    if not m:
        raise ValueError(f"Invalid position string: {s!r}. Use 'X,Y'")
    return int(m.group(1)), int(m.group(2))

def wait_until(display: "wayland.wl_display", predicate, timeout: float, tick: float = 0.05) -> bool:
    """Dispatch events until predicate() is True or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        display.dispatch_timeout(tick)
    return predicate()

# ----- Data holders (fed by protocol events) ----------------------------------

@dataclass
class ModeInfo:
    obj: "wayland.zwlr_output_mode_v1"
    width: Optional[int] = None
    height: Optional[int] = None
    refresh_mHz: Optional[int] = None
    preferred: bool = False
    finished: bool = False

    def pretty(self) -> str:
        if self.width and self.height:
            if self.refresh_mHz:
                hz = self.refresh_mHz / 1000.0
                return f"{self.width}x{self.height}@{hz:.3f}Hz" + (" (preferred)" if self.preferred else "")
            return f"{self.width}x{self.height}" + (" (preferred)" if self.preferred else "")
        return "<mode>"

@dataclass
class HeadInfo:
    obj: "wayland.zwlr_output_head_v1"
    name: Optional[str] = None
    description: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    enabled: Optional[bool] = None
    x: Optional[int] = None
    y: Optional[int] = None
    scale: Optional[float] = None
    transform: Optional[int] = None
    modes: List[ModeInfo] = None
    current_mode: Optional[ModeInfo] = None
    finished: bool = False

    def __post_init__(self):
        if self.modes is None:
            self.modes = []

    def find_mode(self, w: int, h: int, r_mHz: Optional[int]) -> Optional[ModeInfo]:
        cands = [m for m in self.modes if m.width == w and m.height == h and not m.finished]
        if not cands:
            return None
        if r_mHz is None:
            # Prefer 'preferred', else highest refresh, else first
            pref = [m for m in cands if m.preferred and m.refresh_mHz is not None]
            if pref:
                return pref[0]
            best = sorted([m for m in cands if m.refresh_mHz is not None],
                          key=lambda m: m.refresh_mHz, reverse=True)
            return best[0] if best else cands[0]
        # exact refresh match (some compositors round)
        exact = [m for m in cands if m.refresh_mHz == r_mHz]
        if exact:
            return exact[0]
        # If no exact, pick nearest refresh
        with_rate = [m for m in cands if m.refresh_mHz is not None]
        if with_rate:
            return min(with_rate, key=lambda m: abs(m.refresh_mHz - r_mHz))
        return cands[0]

# ----- Wayland classes (python-wayland will instantiate these) ----------------

@wayland_class("wl_registry")
class Registry(wayland.wl_registry):
    def __init__(self):
        super().__init__()
        self.output_manager = None

    def on_global(self, name, interface, version):
        if interface == "zwlr_output_manager_v1":
            # Bind to the announced version; the protocol has versions, but v1 *interface* has sub-versions.
            self.output_manager = self.bind(name, interface, version)

@wayland_class("zwlr_output_manager_v1")
class OutputManager(wayland.zwlr_output_manager_v1):
    def __init__(self):
        super().__init__()
        self.heads: List[HeadInfo] = []
        self.serial: Optional[int] = None
        self.finished: bool = False

    def on_head(self, head):
        # 'head' will be our Head subclass thanks to @wayland_class.
        self.heads.append(head.info)

    def on_done(self, serial):
        self.serial = serial  # serial required for create_configuration()
        # Not a "complete" flag forever — compositor may send done again later on changes.

    def on_finished(self):
        self.finished = True

@wayland_class("zwlr_output_head_v1")
class Head(wayland.zwlr_output_head_v1):
    def __init__(self):
        super().__init__()
        self.info = HeadInfo(obj=self)

    # Properties
    def on_name(self, name): self.info.name = name
    def on_description(self, description): self.info.description = description
    def on_make(self, make): self.info.make = make
    def on_model(self, model): self.info.model = model
    def on_serial_number(self, serial_number): self.info.serial_number = serial_number
    def on_enabled(self, enabled): self.info.enabled = bool(enabled)
    def on_position(self, x, y): self.info.x, self.info.y = x, y
    def on_scale(self, scale): self.info.scale = float(scale)
    def on_transform(self, transform): self.info.transform = int(transform)

    # Mode list
    def on_mode(self, mode):
        # 'mode' becomes our Mode class instance; stash backing info object
        self.info.modes.append(mode.info)

    def on_current_mode(self, mode):
        self.info.current_mode = mode.info

    def on_finished(self):
        self.info.finished = True

@wayland_class("zwlr_output_mode_v1")
class Mode(wayland.zwlr_output_mode_v1):
    def __init__(self):
        super().__init__()
        self.info = ModeInfo(obj=self)

    def on_size(self, width, height):
        self.info.width, self.info.height = int(width), int(height)

    def on_refresh(self, refresh_mHz):
        self.info.refresh_mHz = int(refresh_mHz)

    def on_preferred(self):
        self.info.preferred = True

    def on_finished(self):
        self.info.finished = True

@wayland_class("zwlr_output_configuration_v1")
class Configuration(wayland.zwlr_output_configuration_v1):
    def __init__(self):
        super().__init__()
        self.status: Optional[str] = None

    def on_succeeded(self):
        self.status = "succeeded"

    def on_failed(self):
        self.status = "failed"

    def on_cancelled(self):
        self.status = "cancelled"

# ----- Core logic --------------------------------------------------------------

def list_heads(display: "wayland.wl_display", registry: Registry) -> int:
    mgr: OutputManager = registry.output_manager
    if not mgr:
        print("Compositor doesn't expose zwlr_output_manager_v1 (wlr-output-management).", file=sys.stderr)
        return 2

    # Wait for initial enumeration
    wait_until(display, lambda: mgr.serial is not None and len(mgr.heads) > 0, 2.0)

    for h in mgr.heads:
        if h.finished:
            continue
        title = h.name or "<unnamed>"
        print(f"{title}: {h.description or ''}".strip())
        if h.make or h.model:
            print(f"  Model: {h.make or ''} {h.model or ''}".rstrip())
        if h.serial_number:
            print(f"  S/N  : {h.serial_number}")
        if h.enabled is not None:
            print(f"  State: {'ENABLED' if h.enabled else 'disabled'}")
        if h.x is not None and h.y is not None:
            print(f"  Pos  : {h.x},{h.y}")
        if h.scale is not None:
            print(f"  Scale: {h.scale:g}")
        if h.transform is not None:
            # Render transform name if we know it
            inv = {v: k for k, v in TRANSFORM_STR_TO_ENUM.items()}
            tname = inv.get(h.transform, str(h.transform))
            print(f"  Xform: {tname}")

        # Ensure we've collected mode details
        wait_until(display, lambda: all(m.width and m.height for m in h.modes), 1.0)
        if h.current_mode:
            cur = h.current_mode.pretty()
            print(f"  Mode*: {cur}")
        else:
            print("  Mode*: (unknown)")

        if h.modes:
            print("  Modes:")
            for m in h.modes:
                print(f"    - {m.pretty()}")
        print()

    return 0

def apply_set(
    display: "wayland.wl_display",
    registry: Registry,
    head_name: str,
    mode_str: Optional[str],
    scale: Optional[float],
    pos: Optional[Tuple[int, int]],
    transform_str: Optional[str],
    enable: Optional[bool],
    test_only: bool,
) -> int:
    mgr: OutputManager = registry.output_manager
    if not mgr:
        print("Compositor doesn't expose zwlr_output_manager_v1 (wlr-output-management).", file=sys.stderr)
        return 2

    # Wait for heads + serial
    ok = wait_until(display, lambda: mgr.serial is not None and len(mgr.heads) > 0, 2.0)
    if not ok:
        print("Timed out waiting for output enumeration.", file=sys.stderr)
        return 3

    # Find target head
    target = None
    for h in mgr.heads:
        if h.name == head_name:
            target = h
            break
    if not target:
        print(f"Head {head_name!r} not found. Available heads:", file=sys.stderr)
        for h in mgr.heads:
            print("  -", h.name or "<unnamed>", file=sys.stderr)
        return 4

    # Resolve desired mode (if provided)
    desired_mode_obj = None
    custom_mode = None
    if mode_str:
        w, h, r_mHz = parse_mode_str(mode_str)
        # Wait until the mode list has details
        wait_until(display, lambda: all(m.width and m.height for m in target.modes), 1.0)
        picked = target.find_mode(w, h, r_mHz)
        if picked:
            desired_mode_obj = picked.obj
        else:
            # No native mode — fall back to set_custom_mode
            custom_mode = (w, h, r_mHz or 0)

    # Transform
    transform = None
    if transform_str:
        key = transform_str.strip().lower()
        if key not in TRANSFORM_STR_TO_ENUM:
            raise ValueError(f"Invalid transform {transform_str!r}. "
                             f"Use one of: {', '.join(sorted(TRANSFORM_STR_TO_ENUM))}")
        transform = TRANSFORM_STR_TO_ENUM[key]

    # Build a full configuration (all heads must be included)
    cfg: Configuration = mgr.create_configuration(mgr.serial)

    def enable_and_maybe_configure(h: HeadInfo):
        ch = cfg.enable_head(h.obj)
        # Only set properties we were asked to change; unspecified ones are left as-is.
        if h is target:
            if desired_mode_obj is not None:
                ch.set_mode(desired_mode_obj)
            elif custom_mode is not None:
                w, ht, r = custom_mode
                ch.set_custom_mode(w, ht, r)
            if pos is not None:
                ch.set_position(pos[0], pos[1])
            if transform is not None:
                ch.set_transform(transform)
            if scale is not None:
                ch.set_scale(float(scale))

    for h in mgr.heads:
        # For omitted boolean 'enable', keep current enabled state unless user specified otherwise
        want_enable = h.enabled if enable is None or h is not target else enable
        if want_enable:
            enable_and_maybe_configure(h)
        else:
            cfg.disable_head(h.obj)

    # Apply or test
    if test_only:
        cfg.test()
    else:
        cfg.apply()

    # Wait for result
    ok = wait_until(display, lambda: cfg.status is not None, 3.0)
    if not ok:
        print("No reply to apply/test (timed out).", file=sys.stderr)
        return 5

    print(f"Configuration {cfg.status}.")
    # On 'succeeded', compositor may emit an updated manager 'done' afterwards.
    # We can pump briefly so 'list' prints fresh state on next run.
    display.dispatch_timeout(0.1)
    return 0 if cfg.status == "succeeded" else 6

# ----- CLI --------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Manage outputs via wlr-output-management-unstable-v1")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List heads and their modes")

    p_set = sub.add_parser("set", help="Apply changes to a single head (atomic across all heads)")
    p_set.add_argument("--head", required=True, help="Head name (e.g. DP-1, eDP-1, HDMI-A-1)")
    p_set.add_argument("--mode", help="WxH[@Hz], e.g. 2560x1440@144 or 1920x1080")
    p_set.add_argument("--scale", type=float, help="Scale factor (e.g. 1, 1.25, 2)")
    p_set.add_argument("--pos", help="X,Y position in compositor space (e.g. 0,0 or 1920,0)")
    p_set.add_argument("--transform", help="normal|90|180|270|flipped|flipped-90|flipped-180|flipped-270")
    en = p_set.add_mutually_exclusive_group()
    en.add_argument("--enable", action="store_true", help="Enable the head")
    en.add_argument("--disable", action="store_true", help="Disable the head")
    p_set.add_argument("--test", action="store_true", help="Validate only; do not apply")

    args = p.parse_args(argv)

    # Connect
    display = wayland.wl_display()
    registry: Registry = display.get_registry()

    # Pump a bit so the registry announces globals
    display.dispatch_timeout(0.05)

    if args.cmd == "list":
        return list_heads(display, registry)

    if args.cmd == "set":
        pos = parse_pos_str(args.pos) if args.pos else None
        enable = True if args.enable else (False if args.disable else None)
        try:
            return apply_set(
                display=display,
                registry=registry,
                head_name=args.head,
                mode_str=args.mode,
                scale=args.scale,
                pos=pos,
                transform_str=args.transform,
                enable=enable,
                test_only=args.test,
            )
        except ValueError as ve:
            print(str(ve), file=sys.stderr)
            return 2

    return 0

if __name__ == "__main__":
    sys.exit(main())
