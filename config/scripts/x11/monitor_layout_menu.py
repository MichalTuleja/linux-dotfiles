#!/usr/bin/env python3

import subprocess
import re
import os
import hashlib

def run(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip()

def get_connected_outputs():
    xrandr = run("xrandr")
    outputs = []
    for line in xrandr.splitlines():
        if " connected" in line:
            outputs.append(line.split()[0])
    return outputs

def _parse_edid_vendor_model(edid_hex):
    """Return (vendor, model) parsed from an EDID hex string.

    - `vendor`: 3-letter PNP ID (e.g., 'DEL').
    - `model`: Monitor name from descriptor 0xFC when available,
      otherwise ASCII string descriptor 0xFE, otherwise product code.
    """
    if not edid_hex:
        return (None, None)
    try:
        if isinstance(edid_hex, (bytes, bytearray)):
            b = bytes(edid_hex)
        else:
            s = re.sub(r"\s+", "", str(edid_hex))
            b = bytes.fromhex(s)
    except Exception:
        return (None, None)

    if len(b) < 128:
        return (None, None)

    # Manufacturer (PNP ID): 2 bytes big-endian packed as 5-bit letters
    mfg = (b[8] << 8) | b[9]
    vendor = "".join(chr(((mfg >> shift) & 0x1F) + 64) for shift in (10, 5, 0))

    # Prefer monitor name (descriptor 0xFC); fallback to ASCII string (0xFE)
    def _extract_descriptor_text(block):
        try:
            text = block[5:18].decode("ascii", errors="ignore")
            # EDID strings may include 0x0A as terminator; strip padding
            text = text.split("\x0a")[0].strip().strip("\x00")
            return text or None
        except Exception:
            return None

    model = None
    for off in (54, 72, 90, 108):
        if off + 18 <= len(b):
            desc = b[off : off + 18]
            if desc[0:3] == b"\x00\x00\x00" and desc[3] == 0xFC:
                model = _extract_descriptor_text(desc)
                if model:
                    break

    if not model:
        for off in (54, 72, 90, 108):
            if off + 18 <= len(b):
                desc = b[off : off + 18]
                if desc[0:3] == b"\x00\x00\x00" and desc[3] == 0xFE:
                    model = _extract_descriptor_text(desc)
                    if model:
                        break

    if not model:
        prod_code = b[10] | (b[11] << 8)  # little-endian product code
        model = f"0x{prod_code:04X}"

    return (vendor, model)

def get_outputs_with_vendor_model():
    """Return a list of (output, vendor, model) for connected displays.

    Does not call `xrandr`. Prefers python-xlib (RandR). If unavailable,
    falls back to reading EDID from `/sys/class/drm`.
    """
    # 1) Try python-xlib
    try:
        from Xlib import display as xdisplay
        from Xlib.ext import randr
        from Xlib import X  # noqa: F401

        d = xdisplay.Display()
        root = d.screen().root
        sres = randr.get_screen_resources(root).reply()

        results = []
        for output_id in getattr(sres, "outputs", []) or []:
            try:
                info = randr.get_output_info(root, output_id, sres.config_timestamp).reply()
            except Exception:
                continue
            name = info.name.decode(errors="ignore") if isinstance(info.name, (bytes, bytearray)) else str(info.name)
            connected = getattr(info, "connection", 2) == 0
            if not connected:
                continue

            edid_hex = None
            try:
                props = randr.list_output_properties(root, output_id).reply()
                for atom in getattr(props, "atoms", []) or []:
                    try:
                        name_atom = d.get_atom_name(atom)
                        if str(name_atom).upper() != "EDID":
                            continue
                        pval = randr.get_output_property(
                            root, output_id, atom, X.AnyPropertyType, 0, 10000, False, False
                        ).reply()
                        edid_hex = bytes(pval.data) if hasattr(pval, "data") else None
                        break
                    except Exception:
                        continue
            except Exception:
                pass

            vendor, model = _parse_edid_vendor_model(edid_hex)
            results.append((name, vendor, model))

        try:
            d.close()
        except Exception:
            pass

        if results:
            return results
    except Exception:
        pass

    # 2) Fallback: read from /sys/class/drm
    results = []
    try:
        import glob
        for conn_path in glob.glob("/sys/class/drm/card*-*"):
            base = os.path.basename(conn_path)
            if "-" not in base:
                continue
            name_part = base.split("-", 1)[1]
            name = name_part.replace("HDMI-A-", "HDMI-")

            try:
                with open(os.path.join(conn_path, "status"), "r", encoding="utf-8", errors="ignore") as f:
                    status = f.read().strip().lower()
                if status != "connected":
                    continue
            except Exception:
                continue

            edid_bytes = None
            try:
                with open(os.path.join(conn_path, "edid"), "rb") as f:
                    data = f.read()
                    edid_bytes = data if data else None
            except Exception:
                edid_bytes = None

            vendor, model = _parse_edid_vendor_model(edid_bytes)
            results.append((name, vendor, model))
    except Exception:
        pass

    return results

def outputs_checksum8(outputs):
    """Return an 8-char, lowercase checksum for a list of outputs.

    Accepts list items as tuples like (name, vendor, model) or strings.
    Sorts entries to make the checksum order-independent.
    """
    items = []
    for o in outputs:
        if isinstance(o, (list, tuple)) and len(o) >= 3:
            name, vendor, model = o[0], o[1] or "", o[2] or ""
            items.append(f"{vendor}|{model}|{name}".lower())
        else:
            items.append(str(o).lower())
    items.sort()
    digest = hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()
    return digest[:8]

def get_external_output():
    return next((o for o in get_connected_outputs() if not o.lower().startswith("edp")), None)

def get_native_resolution(output):
    xrandr = run("xrandr")
    in_block = False
    for line in xrandr.splitlines():
        if line.startswith(output):
            in_block = True
        elif re.match(r'^\S', line):  # another output block starts
            in_block = False
        elif in_block and '+' in line:
            match = re.match(r'\s+(\d+x\d+)', line)
            if match:
                return match.group(1)
    return None

def has_resolution(output, res):
    xrandr = run("xrandr")
    in_block = False
    for line in xrandr.splitlines():
        if line.startswith(output):
            in_block = True
        elif re.match(r'^\S', line):
            in_block = False
        elif in_block and res in line:
            return True
    return False

def apply_layout(choice):
    # internal = "eDP-1"
    # external = get_external_output()

    # if not external:
    #     subprocess.run(['notify-send', '❌ No external display found'])
    #     return

    # internal_res = get_native_resolution(internal)
    # if not internal_res:
    #     subprocess.run(['notify-send', '❌ Could not detect internal resolution'])
    #     return

    if choice == " External only":
        subprocess.run(['notify-send', '❌ Not supported'])

    elif choice == " Mirror display":
        subprocess.run(f"autorandr -l common", shell=True)

    elif choice == " Extend to the left":
        subprocess.run(f"autorandr -l horizontal-reverse", shell=True)

    elif choice == " Extend to the right":
        subprocess.run(f"autorandr -l horizontal", shell=True)

    elif choice == " Internal only":
        subprocess.run(f"autorandr -l laptop", shell=True)

    elif choice == " Save current layout":
        lst = get_outputs_with_vendor_model()
        layout_id = outputs_checksum8(lst)
        subprocess.run(f"autorandr -s {layout_id} --force", shell=True)

    elif choice == " Load default layout":
        subprocess.run(f"autorandr -c", shell=True)

def main():
    options = [
        " Mirror display",
        " Internal only",
        " External only",
        " Extend to the right",
        " Extend to the left",
        " Save current layout",
        " Load default layout"
    ]

    menu = '\n'.join(options)
    selected = run(f'echo "{menu}" | rofi -dmenu -i -p " Display Layout"')
    if selected in options:
        apply_layout(selected)

if __name__ == "__main__":
    main()
