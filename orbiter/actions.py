"""
Action Dispatcher for Orbiter
Handles translation from button triggers to uinput events, combos, and window manager commands.
"""
import time
import subprocess
import evdev
from evdev import ecodes as e

# Umfassende Liste aller uinput-Fähigkeiten
ALL_UINPUT_KEYS = [
    # Maustasten
    e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE, e.BTN_SIDE, e.BTN_EXTRA,
    # Standard-Tasten
    e.KEY_ESC, e.KEY_F1, e.KEY_F2, e.KEY_F3, e.KEY_F4, e.KEY_F5, e.KEY_F6,
    e.KEY_F7, e.KEY_F8, e.KEY_F9, e.KEY_F10, e.KEY_F11, e.KEY_F12,
    e.KEY_1, e.KEY_2, e.KEY_3, e.KEY_4, e.KEY_5, e.KEY_6, e.KEY_7, e.KEY_8, e.KEY_9, e.KEY_0,
    e.KEY_A, e.KEY_B, e.KEY_C, e.KEY_D, e.KEY_E, e.KEY_F, e.KEY_G, e.KEY_H, e.KEY_I,
    e.KEY_J, e.KEY_K, e.KEY_L, e.KEY_M, e.KEY_N, e.KEY_O, e.KEY_P, e.KEY_Q, e.KEY_R,
    e.KEY_S, e.KEY_T, e.KEY_U, e.KEY_V, e.KEY_W, e.KEY_X, e.KEY_Y, e.KEY_Z,
    e.KEY_SPACE, e.KEY_ENTER, e.KEY_BACKSPACE, e.KEY_TAB, e.KEY_DELETE,
    e.KEY_UP, e.KEY_DOWN, e.KEY_LEFT, e.KEY_RIGHT, e.KEY_PAGEUP, e.KEY_PAGEDOWN,
    e.KEY_HOME, e.KEY_END,
    # Modifiers
    e.KEY_LEFTCTRL, e.KEY_RIGHTCTRL,
    e.KEY_LEFTALT, e.KEY_RIGHTALT,
    e.KEY_LEFTSHIFT, e.KEY_RIGHTSHIFT,
    e.KEY_LEFTMETA, e.KEY_RIGHTMETA,
    # Media
    e.KEY_VOLUMEUP, e.KEY_VOLUMEDOWN, e.KEY_MUTE, e.KEY_PLAYPAUSE, e.KEY_NEXTSONG, e.KEY_PREVIOUSSONG
]

def resolve_ecode(name_or_code):
    """Löst 'BTN_LEFT' oder 'KEY_D' in den numerischen evdev-Code auf."""
    if isinstance(name_or_code, int):
        return name_or_code
    if hasattr(e, name_or_code):
        return getattr(e, name_or_code)
    return None

def execute_action(action_def, is_press, vmouse, state_callbacks):
    """
    Führt die konfigurierte Aktion aus.
    action_def: dict aus config.json (z.B. {"type": "combo", "action": [...]})
    is_press: bool (True = gedrückt, False = losgelassen)
    vmouse: UInput Instanz
    state_callbacks: dict mit Callback-Funktionen (z.B. speed_up, toggle_2d)
    """
    atype = action_def.get("type", "none")
    action = action_def.get("action")

    if atype == "mouse":
        code = resolve_ecode(action)
        if code:
            vmouse.write(e.EV_KEY, code, 1 if is_press else 0)
            vmouse.syn()

    elif atype == "key":
        code = resolve_ecode(action)
        if code:
            vmouse.write(e.EV_KEY, code, 1 if is_press else 0)
            vmouse.syn()

    elif atype == "combo":
        if is_press and isinstance(action, list):
            # Tasten nacheinander drücken
            codes = [resolve_ecode(k) for k in action if resolve_ecode(k) is not None]
            for c in codes:
                vmouse.write(e.EV_KEY, c, 1)
            vmouse.syn()
            time.sleep(0.02)
            # In umgekehrter Reihenfolge loslassen
            for c in reversed(codes):
                vmouse.write(e.EV_KEY, c, 0)
            vmouse.syn()

    elif atype == "hyprland":
        if is_press and action:
            cmd = f'hyprctl dispatch \'{action}\''
            try:
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as err:
                print(f"[Orbiter] Hyprland Dispatch Fehler: {err}")

    elif atype == "shell":
        if is_press and action:
            try:
                subprocess.Popen(action, shell=True)
            except Exception as err:
                print(f"[Orbiter] Shell Befehl Fehler: {err}")

    elif atype == "builtin":
        if is_press and action in state_callbacks:
            state_callbacks[action]()
