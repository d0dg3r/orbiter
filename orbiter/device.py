"""
Hardware Device Scanner & Connection Handler for 3Dconnexion Devices
"""
import time
import evdev
from evdev import InputDevice

KNOWN_NAMES = [
    "SpaceExplorer",
    "Space Navigator",
    "SpaceMouse",
    "SpacePilot",
    "SpaceTraveler",
    "3Dconnexion"
]

def find_spacemouse_device():
    """Findet die echte physische 3D-Maus (ignoriert uinput-Virtual-Devices)."""
    for path in evdev.list_devices():
        try:
            dev = InputDevice(path)
            # Ignoriere virtuelle uinput Mäuse
            if "Virtual" in dev.name or "Orbiter" in dev.name:
                continue
            for name in KNOWN_NAMES:
                if name.lower() in dev.name.lower():
                    return dev
        except (PermissionError, OSError):
            continue
    return None

def wait_for_device(poll_interval=2.0):
    """Wartet, bis das Gerät eingesteckt wird."""
    while True:
        dev = find_spacemouse_device()
        if dev:
            return dev
        time.sleep(poll_interval)
