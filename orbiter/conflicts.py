"""
Detect conflicts with other SpaceMouse services (especially spacenavd).

spacenavd opens the same HID device exclusively or in competition — Orbiter
then cannot read events reliably. spacenavd must be disabled before the daemon starts.
"""
from __future__ import annotations

import os
import subprocess
from typing import Optional

from orbiter.i18n import tr


def _systemctl_is_active(unit: str, user: bool = False) -> bool:
    cmd = ["systemctl"]
    if user:
        cmd.append("--user")
    cmd.extend(["is-active", "--quiet", unit])
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2.0,
            check=False,
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _process_running(name: str) -> bool:
    """Return True if a process with the exact comm name is running (/proc)."""
    try:
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            comm_path = f"/proc/{entry}/comm"
            try:
                with open(comm_path, "r", encoding="utf-8") as fh:
                    if fh.read().strip() == name:
                        return True
            except (OSError, UnicodeDecodeError):
                continue
    except OSError:
        pass
    return False


def spacenavd_running() -> bool:
    """True when spacenavd is active as a systemd unit or process."""
    if _systemctl_is_active("spacenavd", user=False):
        return True
    if _systemctl_is_active("spacenavd.service", user=False):
        return True
    if _systemctl_is_active("spacenavd", user=True):
        return True
    if _process_running("spacenavd"):
        return True
    return False


def check_spacenavd_conflict() -> Optional[str]:
    """Return an error message if spacenavd is running, else None."""
    if spacenavd_running():
        return tr("conflict.spacenavd")
    return None
