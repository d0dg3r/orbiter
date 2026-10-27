"""
Hardware Device Scanner, Model Database & Connection Handler for 3Dconnexion Devices
Erkennt angeschlossene 3D-Mäuse, deren Tastenanzahl und Modell-Spezifikationen.
"""
import time
import evdev
from evdev import InputDevice

# Bekannte 3Dconnexion Hardware-Modelle mit Tasten-Layouts
# Tasten-Codes basieren auf evdev (256 = BTN_0, 257 = BTN_1, ...)
DEVICE_MODELS = {
    "compact": {
        "id": "compact",
        "name": "SpaceMouse Compact / Wireless",
        "button_count": 2,
        "buttons": {
            "256": {"name": "Taste 1 (Links)", "desc": "Linke Taste"},
            "257": {"name": "Taste 2 (Rechts)", "desc": "Rechte Taste"}
        },
        "default_mapping": {
            "256": {"name": "Linke Maustaste", "type": "mouse", "action": "BTN_LEFT", "description": "Linksklick"},
            "257": {"name": "Rechte Maustaste", "type": "mouse", "action": "BTN_RIGHT", "description": "Rechtsklick"}
        }
    },
    "explorer": {
        "id": "explorer",
        "name": "SpaceExplorer",
        "button_count": 15,
        "buttons": {
            "256": {"name": "1", "desc": "Taste 1"},
            "257": {"name": "2", "desc": "Taste 2"},
            "258": {"name": "T", "desc": "Top Ansicht / Taste T"},
            "259": {"name": "L", "desc": "Left Ansicht / Taste L"},
            "260": {"name": "R", "desc": "Right Ansicht / Taste R"},
            "261": {"name": "F", "desc": "Front Ansicht / Taste F"},
            "262": {"name": "ESC", "desc": "Escape"},
            "263": {"name": "ALT", "desc": "Alt Modifier"},
            "264": {"name": "SHIFT", "desc": "Shift Modifier"},
            "265": {"name": "CTRL", "desc": "Strg Modifier"},
            "266": {"name": "FIT", "desc": "Ansicht einpassen (Fit)"},
            "267": {"name": "PANEL", "desc": "Bedienpanel / Super"},
            "268": {"name": "+", "desc": "Plus / Schneller"},
            "269": {"name": "-", "desc": "Minus / Langsamer"},
            "270": {"name": "2D", "desc": "2D-Modus Umschalter"}
        }
    },
    "pro": {
        "id": "pro",
        "name": "SpaceMouse Pro / Wireless",
        "button_count": 15,
        "buttons": {
            "256": {"name": "Menu", "desc": "Menü-Taste"},
            "257": {"name": "Fit", "desc": "Ansicht zentrieren"},
            "258": {"name": "Top", "desc": "Draufsicht (T)"},
            "259": {"name": "Right", "desc": "Rechtsansicht (R)"},
            "260": {"name": "Front", "desc": "Vorderansicht (F)"},
            "261": {"name": "Roll 90°", "desc": "Drehung im Uhrzeigersinn"},
            "262": {"name": "1", "desc": "Funktionstaste 1"},
            "263": {"name": "2", "desc": "Funktionstaste 2"},
            "264": {"name": "3", "desc": "Funktionstaste 3"},
            "265": {"name": "4", "desc": "Funktionstaste 4"},
            "266": {"name": "Esc", "desc": "Escape"},
            "267": {"name": "Alt", "desc": "Alt-Taste"},
            "268": {"name": "Shift", "desc": "Umschalt-Taste"},
            "269": {"name": "Ctrl", "desc": "Strg-Taste"},
            "270": {"name": "Rot-Toggle", "desc": "Rotation sperren/entsperren"}
        }
    },
    "enterprise": {
        "id": "enterprise",
        "name": "SpaceMouse Enterprise",
        "button_count": 31,
        "buttons": {str(256 + i): {"name": f"Taste {i+1}", "desc": f"Enterprise Button {i+1}"} for i in range(31)}
    }
}

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

def detect_device_model(device=None):
    """
    Ermittelt das Modell des 3Dconnexion-Geräts anhand Name, USB-ID und Tastenanzahl.
    Gibt die Modelldefinition aus DEVICE_MODELS zurück.
    """
    if device is None:
        device = find_spacemouse_device()

    if not device:
        # Fallback auf Standard-SpaceExplorer wenn kein Gerät angeschlossen
        return DEVICE_MODELS["explorer"]

    dev_name = device.name.lower()

    # 1. Erkennung nach Namen
    if "explorer" in dev_name:
        return DEVICE_MODELS["explorer"]
    elif "enterprise" in dev_name:
        return DEVICE_MODELS["enterprise"]
    elif "pro" in dev_name and "wireless" not in dev_name and "compact" not in dev_name:
        return DEVICE_MODELS["pro"]
    elif "compact" in dev_name or "navigator" in dev_name or "wireless" in dev_name:
        # Navigator und Compact haben meist nur 2 Tasten
        caps = device.capabilities().get(evdev.ecodes.EV_KEY, [])
        if len(caps) <= 4:
            return DEVICE_MODELS["compact"]
        return DEVICE_MODELS["compact"]

    # 2. Erkennung nach gemeldeten Tasten (Capabilities)
    caps = device.capabilities().get(evdev.ecodes.EV_KEY, [])
    btn_count = len(caps)
    if btn_count <= 2:
        return DEVICE_MODELS["compact"]
    elif btn_count <= 16:
        return DEVICE_MODELS["explorer"]
    else:
        return DEVICE_MODELS["enterprise"]

def wait_for_device(poll_interval=2.0):
    """Wartet, bis das Gerät eingesteckt wird."""
    while True:
        dev = find_spacemouse_device()
        if dev:
            return dev
        time.sleep(poll_interval)
