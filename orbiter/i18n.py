"""
Dynamic localization for Orbiter (DE/EN/…).

Languages = all files under orbiter/locales/<code>.json.
Fallback catalog: en.json. _meta.native_name for display names.

Language resolution (priority):
  1. ORBITER_LANG environment variable
  2. Config key ui_language (code|auto)
  3. System locale (LANG / LC_MESSAGES)
"""
from __future__ import annotations

import json
import locale
import os
from pathlib import Path
from typing import Any, Callable, Optional

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
_catalog: dict[str, str] = {}
_meta: dict[str, Any] = {}
_lang: str = "en"
_listeners: list[Callable[[str], None]] = []


def _locale_path(code: str) -> Path:
    return _LOCALES_DIR / f"{code}.json"


def available_languages() -> list[str]:
    """All language codes from locales/*.json (excluding leading _)."""
    if not _LOCALES_DIR.is_dir():
        return ["en"]
    codes = sorted(
        p.stem
        for p in _LOCALES_DIR.glob("*.json")
        if p.is_file() and not p.stem.startswith("_")
    )
    if "en" not in codes and not _locale_path("en").is_file():
        # Expect en at minimum — warn only when nothing is present
        if not codes:
            return ["en"]
    elif "en" not in codes:
        codes.append("en")
        codes.sort()
    return codes or ["en"]


def _load_raw(lang: str) -> dict[str, Any]:
    path = _locale_path(lang)
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def _load_catalog(lang: str) -> tuple[dict[str, str], dict[str, Any]]:
    raw = _load_raw(lang)
    meta = raw.get("_meta") if isinstance(raw.get("_meta"), dict) else {}
    catalog = {
        str(k): str(v)
        for k, v in raw.items()
        if k != "_meta" and not isinstance(v, (dict, list))
    }
    return catalog, meta


def language_native_name(code: str) -> str:
    """Display name of the language (_meta.native_name), else the code."""
    raw = _load_raw(code)
    meta = raw.get("_meta") if isinstance(raw.get("_meta"), dict) else {}
    name = meta.get("native_name")
    return str(name) if name else code


def _match_lang_prefix(value: str) -> Optional[str]:
    """Map 'de_CH.UTF-8' / 'en' to a known locale code."""
    val = (value or "").strip().lower().replace("-", "_")
    if not val:
        return None
    codes = available_languages()
    # Exact match
    primary = val.split(".")[0]
    if primary in codes:
        return primary
    # Prefix (de_ch → de)
    short = primary.split("_")[0]
    if short in codes:
        return short
    for code in codes:
        if primary.startswith(code) or short == code:
            return code
    return None


def detect_system_lang() -> str:
    env = (os.environ.get("ORBITER_LANG") or "").strip()
    matched = _match_lang_prefix(env)
    if matched:
        return matched
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        matched = _match_lang_prefix(os.environ.get(key) or "")
        if matched:
            return matched
    try:
        matched = _match_lang_prefix(locale.getdefaultlocale()[0] or "")
        if matched:
            return matched
    except Exception:
        pass
    return "en" if "en" in available_languages() else available_languages()[0]


def resolve_lang(configured: Optional[str] = None) -> str:
    env = (os.environ.get("ORBITER_LANG") or "").strip()
    matched = _match_lang_prefix(env)
    if matched:
        return matched
    cfg = (configured or "auto").strip().lower()
    if cfg and cfg != "auto":
        matched = _match_lang_prefix(cfg)
        if matched:
            return matched
        if cfg in available_languages():
            return cfg
    return detect_system_lang()


def register_listener(callback: Callable[[str], None]) -> None:
    if callback not in _listeners:
        _listeners.append(callback)


def unregister_listener(callback: Callable[[str], None]) -> None:
    if callback in _listeners:
        _listeners.remove(callback)


def _notify_listeners() -> None:
    for cb in list(_listeners):
        try:
            cb(_lang)
        except Exception:
            pass


def set_language(lang: str) -> str:
    """Load the catalog; fill missing keys from en."""
    global _catalog, _meta, _lang
    codes = available_languages()
    lang = (lang or "en").lower()
    if lang not in codes:
        lang = "en" if "en" in codes else codes[0]
    _lang = lang
    _catalog, _meta = _load_catalog(lang)
    if lang != "en":
        base, _ = _load_catalog("en")
        for k, v in base.items():
            _catalog.setdefault(k, v)
    elif not _catalog and not _locale_path("en").is_file():
        import sys
        print("[i18n] Warnung: locales/en.json fehlt", file=sys.stderr)
    _notify_listeners()
    return _lang


def get_language() -> str:
    return _lang


def tr(key: str, **kwargs: Any) -> str:
    """Translate a message key; optional .format(**kwargs)."""
    if not _catalog:
        set_language(detect_system_lang())
    text = _catalog.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def init_from_config(config_mgr=None) -> str:
    configured = None
    if config_mgr is not None:
        try:
            configured = config_mgr.get("ui_language", "auto")
        except Exception:
            configured = "auto"
    return set_language(resolve_lang(configured))
