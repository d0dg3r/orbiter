"""
Hardware device scanner, model database, and connection handler for 3Dconnexion devices.
Detects attached 3D mice, button counts, and model specs.
"""
import time
import evdev
from evdev import InputDevice

from orbiter.i18n import tr

# Known 3Dconnexion models and button layouts
# Button codes follow evdev (256 = BTN_0, 257 = BTN_1, ...)
# Short names = hardware labels (language-neutral); UI text via localized_button_info / locales
DEVICE_MODELS = {
    "compact": {
        "id": "compact",
        "name": "SpaceMouse Compact / Wireless",
        "button_count": 2,
        "buttons": {
            "256": {"name": "1", "desc": ""},
            "257": {"name": "2", "desc": ""}
        },
        "default_mapping": {
            "256": {"name": "BTN_LEFT", "type": "mouse", "action": "BTN_LEFT", "description": ""},
            "257": {"name": "BTN_RIGHT", "type": "mouse", "action": "BTN_RIGHT", "description": ""}
        }
    },
    "explorer": {
        "id": "explorer",
        "name": "SpaceExplorer",
        "button_count": 15,
        "buttons": {
            "256": {"name": "1", "desc": ""},
            "257": {"name": "2", "desc": ""},
            "258": {"name": "T", "desc": ""},
            "259": {"name": "L", "desc": ""},
            "260": {"name": "R", "desc": ""},
            "261": {"name": "F", "desc": ""},
            "262": {"name": "ESC", "desc": ""},
            "263": {"name": "ALT", "desc": ""},
            "264": {"name": "SHIFT", "desc": ""},
            "265": {"name": "CTRL", "desc": ""},
            "266": {"name": "FIT", "desc": ""},
            "267": {"name": "PANEL", "desc": ""},
            "268": {"name": "+", "desc": ""},
            "269": {"name": "-", "desc": ""},
            "270": {"name": "2D", "desc": ""}
        }
    },
    "pro": {
        "id": "pro",
        "name": "SpaceMouse Pro / Wireless",
        "button_count": 15,
        "buttons": {
            "256": {"name": "Menu", "desc": ""},
            "257": {"name": "Fit", "desc": ""},
            "258": {"name": "Top", "desc": ""},
            "259": {"name": "Right", "desc": ""},
            "260": {"name": "Front", "desc": ""},
            "261": {"name": "Roll 90°", "desc": ""},
            "262": {"name": "1", "desc": ""},
            "263": {"name": "2", "desc": ""},
            "264": {"name": "3", "desc": ""},
            "265": {"name": "4", "desc": ""},
            "266": {"name": "Esc", "desc": ""},
            "267": {"name": "Alt", "desc": ""},
            "268": {"name": "Shift", "desc": ""},
            "269": {"name": "Ctrl", "desc": ""},
            "270": {"name": "Rot-Toggle", "desc": ""}
        }
    },
    "enterprise": {
        "id": "enterprise",
        "name": "SpaceMouse Enterprise",
        "button_count": 31,
        "buttons": {str(256 + i): {"name": str(i + 1), "desc": ""} for i in range(31)}
    }
}


def localized_button_info(code, fallback=None):
    """Hardware short name plus translated description for the UI."""
    fb = fallback or {}
    code_s = str(code)
    name = fb.get("name") or tr(f"device.btn.{code_s}.name")
    if name == f"device.btn.{code_s}.name":
        name = code_s
    desc = tr(f"device.btn.{code_s}.desc")
    if desc == f"device.btn.{code_s}.desc":
        desc = fb.get("desc") or ""
    return {"name": name, "desc": desc}


KNOWN_NAMES = [
    "SpaceExplorer",
    "Space Navigator",
    "SpaceMouse",
    "SpacePilot",
    "SpaceTraveler",
    "3Dconnexion"
]

def find_spacemouse_device():
    """Find the physical 3D mouse (ignore uinput virtual devices)."""
    for path in evdev.list_devices():
        try:
            dev = InputDevice(path)
            # Skip virtual uinput mice
            if "Virtual" in dev.name or "Orbiter" in dev.name:
                continue
            for name in KNOWN_NAMES:
                if name.lower() in dev.name.lower():
                    return dev
        except (PermissionError, OSError):
            continue
    return None

def detect_device_model(device=None):
    """
    Detect the 3Dconnexion model from name, USB id, and button count.
    Returns the entry from DEVICE_MODELS.
    """
    if device is None:
        device = find_spacemouse_device()

    if not device:
        # Default to SpaceExplorer when no device is connected
        return DEVICE_MODELS["explorer"]

    dev_name = device.name.lower()

    # 1. Match by device name
    if "explorer" in dev_name:
        return DEVICE_MODELS["explorer"]
    elif "enterprise" in dev_name:
        return DEVICE_MODELS["enterprise"]
    elif "pro" in dev_name and "compact" not in dev_name:
        # SpaceMouse Pro and Pro Wireless (many buttons)
        return DEVICE_MODELS["pro"]
    elif "compact" in dev_name or "navigator" in dev_name:
        return DEVICE_MODELS["compact"]
    elif "wireless" in dev_name:
        # Generic "Wireless" without Pro: use button count
        caps = device.capabilities().get(evdev.ecodes.EV_KEY, [])
        if len(caps) > 4:
            return DEVICE_MODELS["pro"]
        return DEVICE_MODELS["compact"]

    # 2. Match by reported buttons (capabilities)
    caps = device.capabilities().get(evdev.ecodes.EV_KEY, [])
    btn_count = len(caps)
    if btn_count <= 2:
        return DEVICE_MODELS["compact"]
    elif btn_count <= 16:
        return DEVICE_MODELS["explorer"]
    else:
        return DEVICE_MODELS["enterprise"]

def wait_for_device(poll_interval=2.0):
    """Block until a device is plugged in."""
    while True:
        dev = find_spacemouse_device()
        if dev:
            return dev
        time.sleep(poll_interval)
