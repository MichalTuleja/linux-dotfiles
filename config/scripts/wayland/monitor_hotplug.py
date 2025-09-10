#!/usr/bin/python3
"""
monitor_hotplug.py – react to display hot-plug events.

Fixed for pyudev ≥ 0.21 (single-arg callback).
"""

import logging
import subprocess
import sys
import time
import signal
from pathlib import Path
import os

try:
    import pyudev
except ImportError:
    sys.stderr.write("pyudev not found – install it with:  pip install pyudev\n")
    sys.exit(1)


# ---------- custom reaction ------------------------------------------------ #

def reaction(connector: str | None = None) -> None:
    """
    Run the helper inside the *same* session environment.
    """
    logging.info("Display change (%s) – applying layout", connector or "?")

    script = Path.home() / "display_monitor_plain.py"
    env = os.environ.copy()  # preserves WAYLAND_DISPLAY, XDG_RUNTIME_DIR, etc.

    try:
        subprocess.run([sys.executable, str(script), "--apply"], check=True, env=env)
    except FileNotFoundError:
        logging.error("Helper not found: %s", script)
    except subprocess.CalledProcessError as exc:
        logging.error("Helper failed: %s", exc)


# ---------- udev glue ------------------------------------------------------ #
def handle_event(*args):
    if len(args) == 1:  # pyudev ≥ 0.21
        device = args[0]
        action = getattr(device, "action", None)
    else:               # legacy pyudev
        action, device = args

    if action != "change":
        return
    if device.properties.get("HOTPLUG") != "1":
        return
    if device.subsystem != "drm":  # paranoia if filter() is missing
        return

    connector = device.sys_name  # e.g. card0-HDMI-A-1
    logging.debug("Hot-plug on %s", connector)
    reaction(connector)


# ---------- graceful shutdown --------------------------------------------- #
_stop = False

def shutdown_handler(signum, frame):
    global _stop
    logging.info("Received signal %s – exiting...", signum)
    _stop = True


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Register signal handlers
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem="drm")

    observer = pyudev.MonitorObserver(monitor, callback=handle_event,
                                      name="udev-monitor-observer")
    observer.start()

    reaction()

    logging.info("Listening for monitor hot-plug events… (Ctrl-C or SIGTERM to quit)")
    try:
        while not _stop:
            time.sleep(1)
    finally:
        observer.stop()
        logging.info("Observer stopped. Bye.")


if __name__ == "__main__":
    main()
