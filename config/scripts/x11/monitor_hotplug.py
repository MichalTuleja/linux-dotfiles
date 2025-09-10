#!/usr/bin/python3
"""
monitor_hotplug.py – react to display hot-plug events.

Fixed for pyudev ≥ 0.21 (single-arg callback).

Usage (X11):
  # Run a shell command on change (and once on start):
  python3 scripts/x11/monitor_hotplug.py --cmd 'autorandr -c && polybar-msg cmd restart'

If --cmd is not provided, it defaults to:  autorandr -c
"""

import argparse
import logging
import subprocess
import sys
import time
import signal
from pathlib import Path
import shlex
import os

try:
    import pyudev
except ImportError:
    sys.stderr.write("pyudev not found – install it with:  pip install pyudev\n")
    sys.exit(1)


# ---------- custom reaction ------------------------------------------------ #

RUN_CMD: str | None = None  # set by main()

def reaction(connector: str | None = None) -> None:
    """
    Run the helper inside the *same* session environment.
    """
    logging.info("Display change (%s) – running command", connector or "?")

    # Preserve DISPLAY, XAUTHORITY, etc., from the current X11 session
    env = os.environ.copy()

    # Determine the command to run
    cmd = RUN_CMD or "autorandr -c"

    res = subprocess.run(cmd, shell=True, env=env)
    if res.returncode != 0:
        logging.error("Command failed (%d): %s", res.returncode, cmd)
    else:
        logging.info("Command completed: %s", cmd)


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
    global RUN_CMD
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Monitor hot-plug watcher (X11)")
    parser.add_argument(
        "--cmd",
        help="Shell command to run on change (default: 'autorandr -c')",
    )
    args = parser.parse_args()
    RUN_CMD = args.cmd

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
