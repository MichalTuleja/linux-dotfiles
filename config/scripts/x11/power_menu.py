#!/usr/bin/env python3

import os
import subprocess


def run(cmd):
    return subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip()


def _has_cmd(cmd):
    return subprocess.run(f"command -v {cmd} >/dev/null 2>&1", shell=True).returncode == 0


def _notify(msg):
    try:
        subprocess.run(["notify-send", msg])
    except Exception:
        pass


def do_logout():
    # Try compositor/WM-specific exits first, then fall back to logind.
    # Openbox
    if _has_cmd("openbox") and subprocess.run("pgrep -x openbox >/dev/null", shell=True).returncode == 0:
        subprocess.run(["openbox", "--exit"])  # best-effort
        return
    
    # i3
    if _has_cmd("i3-msg") and subprocess.run(["i3-msg", "-t", "get_version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        subprocess.run(["i3-msg", "exit"])  # best-effort
        return

    # Sway
    if _has_cmd("swaymsg") and os.environ.get("SWAYSOCK"):
        subprocess.run(["swaymsg", "exit"])  # best-effort
        return

    # Fallback: terminate the current systemd-logind session
    session_id = os.environ.get("XDG_SESSION_ID", "")
    if session_id:
        subprocess.run(["loginctl", "terminate-session", session_id])
    else:
        # As a last resort, kill the user session (can be harsh)
        uid = os.getuid()
        subprocess.run(["loginctl", "kill-user", str(uid)])


def do_systemctl(action, label):
    rc = subprocess.run(["systemctl", action]).returncode
    if rc != 0:
        _notify(f"❌ Failed to {label}")


def apply_action(choice):
    if choice == " Logout":
        do_logout()
    elif choice == " Sleep":
        do_systemctl("suspend", "sleep")
    elif choice == " Hybrid-sleep":
        do_systemctl("hybrid-sleep", "hybrid-sleep")
    elif choice == " Hibernate":
        do_systemctl("hibernate", "hibernate")
    elif choice == " Shutdown":
        do_systemctl("poweroff", "shutdown")


def main():
    options = [
        " Logout",
        " Sleep",
        " Hybrid-sleep",
        " Hibernate",
        " Shutdown",
    ]

    menu = "\n".join(options)
    selected = run(f'echo "{menu}" | rofi -dmenu -i -p "Power"')
    if selected in options:
        apply_action(selected)


if __name__ == "__main__":
    main()

