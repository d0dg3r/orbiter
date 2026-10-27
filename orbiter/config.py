"""
Orbiter Configuration Manager
Loads, validates, and saves configuration settings from ~/.config/orbiter/config.json
"""
import os
import json
import time
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "orbiter"
CONFIG_FILE = CONFIG_DIR / "config.json"
IPC_SOCKET = CONFIG_DIR / "orbiter.sock"

# 1. Default profile for generic Linux desktops (GNOME, KDE, Wayland, X11)
DEFAULT_PROFILE_SETTINGS = {
    "deadzone": 18,
    "base_speed": 0.05,
    "scroll_deadzone_twist": 90,
    "scroll_speed": 0.003,
    "move_cooldown": 0.15,
    "mode_2d": True,
    "tilt_blend": 0.4,
    "lift_scroll_enabled": True,
    "scroll_deadzone_lift": 90,
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
            "name": "Mitteltaste",
            "type": "mouse",
            "action": "BTN_MIDDLE",
            "description": "Mittlere Maustaste / Radklick"
        },
        "256": {
            "name": "Zurück (1)",
            "type": "mouse",
            "action": "BTN_SIDE",
            "description": "Browser / Dateimanager Zurück"
        },
        "257": {
            "name": "Vorwärts (2)",
            "type": "mouse",
            "action": "BTN_EXTRA",
            "description": "Browser / Dateimanager Vorwärts"
        },
        "267": {
            "name": "PANEL",
            "type": "key",
            "action": "KEY_LEFTMETA",
            "description": "Super / Startmenü / App-Starter"
        },
        "258": {
            "name": "T",
            "type": "key",
            "action": "KEY_T",
            "description": "Standard Taste T"
        },
        "266": {
            "name": "FIT",
            "type": "key",
            "action": "KEY_HOME",
            "description": "Ansicht zentrieren (Pos1 / Home)"
        },
        "270": {
            "name": "2D",
            "type": "builtin",
            "action": "toggle_2d",
            "description": "2D-Präzisionsmodus Toggle"
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
        "262": {
            "name": "ESC",
            "type": "key",
            "action": "KEY_ESC",
            "description": "Escape-Taste"
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

# Shipped defaults: Standard, CAD / 3D, Browser / Medien only.
# Personal profiles (e.g. Hyprland / Joe) live only in the user's config.json.

DEFAULT_PROFILES = {
    "Standard": DEFAULT_PROFILE_SETTINGS,
    "CAD / 3D": {
        "deadzone": 16,
        "base_speed": 0.055,
        "scroll_deadzone_twist": 80,
        "scroll_speed": 0.0035,
        "move_cooldown": 0.12,
        "mode_2d": False,
        "tilt_blend": 0.4,
        "lift_scroll_enabled": True,
        "scroll_deadzone_lift": 90,
        "buttons": {
            "259": {
                "name": "Linksklick",
                "type": "mouse",
                "action": "BTN_LEFT",
                "description": "Auswählen"
            },
            "260": {
                "name": "Rechtsklick",
                "type": "mouse",
                "action": "BTN_RIGHT",
                "description": "Kontextmenü"
            },
            "261": {
                "name": "Mittelklick",
                "type": "mouse",
                "action": "BTN_MIDDLE",
                "description": "3D Drehen / Pan"
            },
            "266": {
                "name": "FIT",
                "type": "key",
                "action": "KEY_HOME",
                "description": "Ansicht zentrieren (Pos1/Home)"
            },
            "270": {
                "name": "2D",
                "type": "builtin",
                "action": "toggle_2d",
                "description": "2D/3D Umschalten"
            },
            "268": {
                "name": "+",
                "type": "builtin",
                "action": "speed_up",
                "description": "Zeiger schneller"
            },
            "269": {
                "name": "-",
                "type": "builtin",
                "action": "speed_down",
                "description": "Zeiger langsamer"
            },
            "262": {
                "name": "ESC",
                "type": "key",
                "action": "KEY_ESC",
                "description": "Abbrechen / Escape"
            },
            "264": {
                "name": "SHIFT",
                "type": "key",
                "action": "KEY_LEFTSHIFT",
                "description": "Shift für Pan-Kombination"
            },
            "265": {
                "name": "CTRL",
                "type": "builtin",
                "action": "next_profile",
                "description": "Nächstes Profil aktivieren"
            }
        }
    },
    "Browser / Medien": {
        "deadzone": 20,
        "base_speed": 0.06,
        "scroll_deadzone_twist": 85,
        "scroll_speed": 0.004,
        "move_cooldown": 0.15,
        "mode_2d": True,
        "tilt_blend": 0.4,
        "lift_scroll_enabled": True,
        "scroll_deadzone_lift": 90,
        "buttons": {
            "259": {
                "name": "Linksklick",
                "type": "mouse",
                "action": "BTN_LEFT",
                "description": "Klick"
            },
            "260": {
                "name": "Rechtsklick",
                "type": "mouse",
                "action": "BTN_RIGHT",
                "description": "Kontextmenü"
            },
            "261": {
                "name": "Neuer Tab",
                "type": "combo",
                "action": ["KEY_LEFTCTRL", "KEY_T"],
                "description": "Strg + T (Neuer Tab)"
            },
            "262": {
                "name": "Tab Schließen",
                "type": "combo",
                "action": ["KEY_LEFTCTRL", "KEY_W"],
                "description": "Strg + W (Tab schließen)"
            },
            "256": {
                "name": "Zurück",
                "type": "mouse",
                "action": "BTN_SIDE",
                "description": "Browser Zurück"
            },
            "257": {
                "name": "Vorwärts",
                "type": "mouse",
                "action": "BTN_EXTRA",
                "description": "Browser Vorwärts"
            },
            "266": {
                "name": "Play/Pause",
                "type": "key",
                "action": "KEY_PLAYPAUSE",
                "description": "Medien Play/Pause"
            },
            "268": {
                "name": "Lauter",
                "type": "key",
                "action": "KEY_VOLUMEUP",
                "description": "Lautstärke erhöhen"
            },
            "269": {
                "name": "Leiser",
                "type": "key",
                "action": "KEY_VOLUMEDOWN",
                "description": "Lautstärke verringern"
            },
            "270": {
                "name": "Mute",
                "type": "key",
                "action": "KEY_MUTE",
                "description": "Stummschalten"
            },
            "265": {
                "name": "CTRL",
                "type": "builtin",
                "action": "next_profile",
                "description": "Nächstes Profil aktivieren"
            }
        }
    }
}

DEFAULT_CONFIG = {
    "device_name_pattern": "Space",
    "active_profile": "Standard",
    "device_model_override": "auto",  # 'auto', 'compact', 'explorer', 'pro', 'enterprise'
    "auto_switch_enabled": True,
    "auto_rules": {
        "CAD / 3D": ["freecad", "org.freecadweb.freecad", "blender", "gimp", "inkscape", "kicad", "prusa-slicer", "bambu-studio"],
        "Browser / Medien": ["chromium", "firefox", "brave-browser", "google-chrome", "zen", "spotify", "vlc"],
    },
    "profiles": DEFAULT_PROFILES
}

PROFILE_SETTINGS_KEYS = {
    "deadzone", "base_speed", "scroll_deadzone_twist",
    "scroll_speed", "move_cooldown", "mode_2d",
    "tilt_blend", "lift_scroll_enabled", "scroll_deadzone_lift",
    "buttons",
}

# Reject giant imports before json.load (DoS / memory)
MAX_CONFIG_BYTES = 2 * 1024 * 1024


def _write_json_secure(path: Path, data: dict):
    """Atomic write with mode 0600 (config may contain shell actions)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(
        str(tmp_file),
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            f.write("\n")
        os.chmod(tmp_file, 0o600)
        tmp_file.replace(path)
    except Exception:
        try:
            tmp_file.unlink(missing_ok=True)
        except Exception:
            pass
        raise


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
            self._sync_active_profile_to_root()
            self.save()
            return self.config

        try:
            file_size = self.path.stat().st_size
            if file_size > MAX_CONFIG_BYTES:
                raise ValueError(f"Config too large ({file_size} bytes)")

            with open(self.path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            self.last_mtime = self.path.stat().st_mtime
            migrated = False

            # Migration: legacy config.json without "profiles"
            if "profiles" not in self.config or not isinstance(self.config["profiles"], dict):
                migrated_buttons = self.config.get("buttons", DEFAULT_PROFILE_SETTINGS["buttons"])
                standard_profile = {
                    "deadzone": self.config.get("deadzone", 18),
                    "base_speed": self.config.get("base_speed", 0.05),
                    "scroll_deadzone_twist": self.config.get("scroll_deadzone_twist", 90),
                    "scroll_speed": self.config.get("scroll_speed", 0.003),
                    "move_cooldown": self.config.get("move_cooldown", 0.15),
                    "mode_2d": self.config.get("mode_2d", True),
                    "tilt_blend": self.config.get("tilt_blend", 0.4),
                    "lift_scroll_enabled": self.config.get("lift_scroll_enabled", True),
                    "scroll_deadzone_lift": self.config.get("scroll_deadzone_lift", 90),
                    "buttons": migrated_buttons
                }
                self.config["profiles"] = {
                    "Standard": standard_profile
                }
                migrated = True

            # Ensure shipped default profiles exist (never remove user-only profiles)
            profiles = self.config.setdefault("profiles", {})
            for prof_name, prof_data in DEFAULT_PROFILES.items():
                if prof_name not in profiles:
                    profiles[prof_name] = json.loads(json.dumps(prof_data))
                    migrated = True

            # Ensure active_profile is valid
            if "active_profile" not in self.config or self.config["active_profile"] not in self.config["profiles"]:
                first_prof = next(iter(self.config["profiles"].keys()), "Standard")
                self.config["active_profile"] = first_prof
                migrated = True

            # Fill missing profile fields from defaults
            for p_name, p_data in self.config["profiles"].items():
                if not isinstance(p_data, dict):
                    continue
                for k, v in DEFAULT_PROFILE_SETTINGS.items():
                    if k not in p_data:
                        p_data[k] = json.loads(json.dumps(v))
                        migrated = True

            self._sync_active_profile_to_root()
            if migrated:
                self.save()

        except Exception as e:
            print(f"[Config] Fehler beim Laden ({e}), lade Standardwerte.")
            # Pin mtime so the 60 Hz daemon ticker does not reload every frame
            try:
                self.last_mtime = self.path.stat().st_mtime if self.path.exists() else time.time()
            except Exception:
                self.last_mtime = time.time()
            self.config = json.loads(json.dumps(DEFAULT_CONFIG))
            self._sync_active_profile_to_root()
        return self.config

    def _sync_active_profile_to_root(self):
        """Mirror active profile settings to top-level keys for backward compatibility."""
        active_data = self.get_active_profile_data()
        for k in PROFILE_SETTINGS_KEYS:
            if k in active_data:
                self.config[k] = active_data[k]

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
        self._sync_active_profile_to_root()
        _write_json_secure(self.path, self.config)
        self.last_mtime = self.path.stat().st_mtime

    def export_config(self, path):
        """Write current config as pretty JSON to path."""
        path = Path(path).expanduser()
        self._sync_active_profile_to_root()
        _write_json_secure(path, self.config)
        return path

    def import_config(self, path, backup=True):
        """
        Load config from path, validate structure, replace live config.
        Backs up to config.json.bak-<timestamp> before overwrite when backup=True.
        """
        path = Path(path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(str(path))
        file_size = path.stat().st_size
        if file_size > MAX_CONFIG_BYTES:
            raise ValueError(f"Config too large ({file_size} bytes, max {MAX_CONFIG_BYTES})")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Config root must be a JSON object")
        profiles = data.get("profiles")
        if not isinstance(profiles, dict) or not profiles:
            raise ValueError("Config must contain a non-empty 'profiles' object")
        active = data.get("active_profile")
        if not active or active not in profiles:
            data["active_profile"] = next(iter(profiles.keys()))

        if backup and self.path.exists():
            from datetime import datetime
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            bak = self.path.with_name(f"config.json.bak-{stamp}")
            # Raw copy preserves current file even if it is not valid JSON
            data_bytes = self.path.read_bytes()
            fd = os.open(str(bak), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                os.write(fd, data_bytes)
            finally:
                os.close(fd)
            os.chmod(bak, 0o600)

        self.config = data
        self._sync_active_profile_to_root()
        self.save()
        return self.config

    def get_profiles(self):
        return self.config.setdefault("profiles", {})

    def get_active_profile_name(self):
        return self.config.get("active_profile", "Standard")

    def get_active_profile_data(self):
        profiles = self.get_profiles()
        active_name = self.get_active_profile_name()
        if active_name not in profiles:
            if not profiles:
                profiles["Standard"] = json.loads(json.dumps(DEFAULT_PROFILE_SETTINGS))
            active_name = next(iter(profiles.keys()))
            self.config["active_profile"] = active_name
        return profiles[active_name]

    def set_active_profile(self, name):
        profiles = self.get_profiles()
        if name in profiles:
            self.config["active_profile"] = name
            self._sync_active_profile_to_root()
            self.save()
            return name
        return self.get_active_profile_name()

    def next_profile(self):
        profiles = list(self.get_profiles().keys())
        if not profiles:
            return "Standard"
        cur = self.get_active_profile_name()
        idx = profiles.index(cur) if cur in profiles else 0
        new_name = profiles[(idx + 1) % len(profiles)]
        self.set_active_profile(new_name)
        return new_name

    def prev_profile(self):
        profiles = list(self.get_profiles().keys())
        if not profiles:
            return "Standard"
        cur = self.get_active_profile_name()
        idx = profiles.index(cur) if cur in profiles else 0
        new_name = profiles[(idx - 1) % len(profiles)]
        self.set_active_profile(new_name)
        return new_name

    def create_profile(self, name, copy_from=None):
        name = name.strip()
        if not name:
            return None
        profiles = self.get_profiles()
        if name in profiles:
            return None

        if copy_from and copy_from in profiles:
            source = profiles[copy_from]
        else:
            source = self.get_active_profile_data()

        profiles[name] = json.loads(json.dumps(source))
        self.set_active_profile(name)
        return name

    def delete_profile(self, name):
        profiles = self.get_profiles()
        if len(profiles) <= 1 or name not in profiles:
            return False
        del profiles[name]
        if self.get_active_profile_name() == name:
            new_active = next(iter(profiles.keys()))
            self.set_active_profile(new_active)
        else:
            self.save()
        return True

    def rename_profile(self, old_name, new_name):
        new_name = new_name.strip()
        profiles = self.get_profiles()
        if not new_name or old_name not in profiles or new_name in profiles:
            return False

        profiles[new_name] = profiles.pop(old_name)
        if self.get_active_profile_name() == old_name:
            self.config["active_profile"] = new_name
            self._sync_active_profile_to_root()
        self.save()
        return True

    def get(self, key, default=None):
        if key in PROFILE_SETTINGS_KEYS:
            active_data = self.get_active_profile_data()
            if key in active_data:
                return active_data[key]
        return self.config.get(key, default)

    def set(self, key, value):
        if key in PROFILE_SETTINGS_KEYS:
            active_data = self.get_active_profile_data()
            active_data[key] = value
        self.config[key] = value

    def get_auto_rules(self):
        """Return profile name -> list of window pattern strings."""
        return self.config.setdefault("auto_rules", {
            "CAD / 3D": ["freecad", "org.freecadweb.freecad", "blender", "gimp", "inkscape", "kicad", "prusa-slicer", "bambu-studio"],
            "Browser / Medien": ["chromium", "firefox", "brave-browser", "google-chrome", "zen", "spotify", "vlc"],
        })

    def is_auto_switch_enabled(self):
        return self.config.get("auto_switch_enabled", True)

    def set_auto_switch_enabled(self, enabled: bool):
        self.config["auto_switch_enabled"] = bool(enabled)
        self.save()

    def get_profile_for_window(self, win_class: str, win_title: str = ""):
        """Pick a profile from window class or title."""
        if not self.is_auto_switch_enabled() or not win_class:
            return None
        c_lower = win_class.lower()
        t_lower = (win_title or "").lower()
        rules = self.get_auto_rules()
        for prof_name, patterns in rules.items():
            if prof_name not in self.get_profiles():
                continue
            for pat in patterns:
                pat_lower = pat.lower().strip()
                if not pat_lower:
                    continue
                if pat_lower in c_lower or (t_lower and pat_lower in t_lower):
                    return prof_name
        return None

    def add_rule_for_profile(self, profile_name: str, pattern: str):
        pattern = pattern.strip().lower()
        if not pattern:
            return False
        rules = self.get_auto_rules()
        patterns = rules.setdefault(profile_name, [])
        if pattern not in patterns:
            patterns.append(pattern)
            self.save()
            return True
        return False

    def remove_rule_for_profile(self, profile_name: str, pattern: str):
        pattern = pattern.strip().lower()
        rules = self.get_auto_rules()
        patterns = rules.get(profile_name, [])
        if pattern in patterns:
            patterns.remove(pattern)
            self.save()
            return True
        return False

    def get_model_override(self):
        return self.config.get("device_model_override", "auto")

    def set_model_override(self, model_id: str):
        self.config["device_model_override"] = model_id
        self.save()

