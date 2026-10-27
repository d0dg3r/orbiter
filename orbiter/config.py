"""
Orbiter Configuration Manager
Loads, validates, and saves configuration settings from ~/.config/orbiter/config.json
"""
import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "orbiter"
CONFIG_FILE = CONFIG_DIR / "config.json"
IPC_SOCKET = CONFIG_DIR / "orbiter.sock"

DEFAULT_CONFIG = {
    "device_name_pattern": "Space",
    "deadzone": 18,
    "base_speed": 0.05,
    "scroll_deadzone_twist": 90,
    "scroll_speed": 0.003,
    "move_cooldown": 0.15,
    "mode_2d": True,
    "buttons": {
        "259": {
            "name": "Linke Maustaste",
            "type": "mouse",
            "action": "BTN_LEFT",
            "description": "Standard Linksklick"
        },
        "260": {
            "name": "Rechte Maustaste",
            "type": "mouse",
            "action": "BTN_RIGHT",
            "description": "Standard Rechtsklick"
        },
        "261": {
            "name": "F",
            "type": "mouse",
            "action": "BTN_MIDDLE",
            "description": "Mittlere Maustaste"
        },
        "267": {
            "name": "PANEL",
            "type": "combo",
            "action": ["KEY_LEFTMETA", "KEY_D"],
            "description": "Super + D (App-Starter / Rofi)"
        },
        "258": {
            "name": "T",
            "type": "combo",
            "action": ["KEY_LEFTMETA", "KEY_U"],
            "description": "Super + U (Ablage / Special Workspace)"
        },
        "256": {
            "name": "1",
            "type": "hyprland",
            "action": "hl.dsp.focus({ workspace = 'e-1' })",
            "description": "Workspace LINKS"
        },
        "257": {
            "name": "2",
            "type": "hyprland",
            "action": "hl.dsp.focus({ workspace = 'e+1' })",
            "description": "Workspace RECHTS"
        },
        "268": {
            "name": "+",
            "type": "builtin",
            "action": "speed_up",
            "description": "Zeiger schneller (+25%)"
        },
        "269": {
            "name": "-",
            "type": "builtin",
            "action": "speed_down",
            "description": "Zeiger langsamer (-20%)"
        },
        "266": {
            "name": "FIT",
            "type": "key",
            "action": "KEY_F11",
            "description": "Vollbild an/aus (F11)"
        },
        "270": {
            "name": "2D",
            "type": "builtin",
            "action": "toggle_2d",
            "description": "2D-Präzisionsmodus Toggle"
        },
        "262": {
            "name": "ESC",
            "type": "key",
            "action": "KEY_ESC",
            "description": "Escape"
        },
        "263": {
            "name": "ALT",
            "type": "key",
            "action": "KEY_LEFTALT",
            "description": "Alt-Taste"
        },
        "264": {
            "name": "SHIFT",
            "type": "key",
            "action": "KEY_LEFTSHIFT",
            "description": "Shift-Taste"
        },
        "265": {
            "name": "CTRL",
            "type": "key",
            "action": "KEY_LEFTCTRL",
            "description": "Strg-Taste"
        }
    }
}

class ConfigManager:
    def __init__(self, path=CONFIG_FILE):
        self.path = Path(path)
        self.config = {}
        self.last_mtime = 0
        self.load()

    def load(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()
            return self.config

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.last_mtime = self.path.stat().st_mtime
            # Ensure defaults for missing keys
            for k, v in DEFAULT_CONFIG.items():
                if k not in self.config:
                    self.config[k] = v
        except Exception as e:
            print(f"[Config] Fehler beim Laden ({e}), lade Standardwerte.")
            self.config = json.loads(json.dumps(DEFAULT_CONFIG))
        return self.config

    def is_modified(self):
        try:
            if not self.path.exists():
                return False
            mtime = self.path.stat().st_mtime
            return mtime > self.last_mtime
        except Exception:
            return False

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp_file = self.path.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        tmp_file.replace(self.path)
        self.last_mtime = self.path.stat().st_mtime

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
