"""
Einfache DE/EN-Lokalisierung für Orbiter.

Sprache aus (Priorität):
  1. Umgebungsvariable ORBITER_LANG (de|en)
  2. Config-Schlüssel ui_language (de|en|auto)
  3. System-Locale (LANG / LC_MESSAGES)
"""
from __future__ import annotations

import json
import locale
import os
from pathlib import Path
from typing import Any, Optional

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"
_catalog: dict[str, str] = {}
_lang: str = "en"


def available_languages() -> list[str]:
    return ["de", "en"]


def detect_system_lang() -> str:
    env = (os.environ.get("ORBITER_LANG") or "").strip().lower()
    if env.startswith("de"):
        return "de"
    if env.startswith("en"):
        return "en"
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = (os.environ.get(key) or "").lower()
        if val.startswith("de"):
            return "de"
        if val.startswith("en"):
            return "en"
    try:
        loc = (locale.getdefaultlocale()[0] or "").lower()
        if loc.startswith("de"):
            return "de"
    except Exception:
        pass
    return "en"


def resolve_lang(configured: Optional[str] = None) -> str:
    env = (os.environ.get("ORBITER_LANG") or "").strip().lower()
    if env.startswith("de"):
        return "de"
    if env.startswith("en"):
        return "en"
    cfg = (configured or "auto").strip().lower()
    if cfg in ("de", "en"):
        return cfg
    return detect_system_lang()


def _load_catalog(lang: str) -> dict[str, str]:
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # flatten nested dicts with dot keys optional — we use flat keys
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def set_language(lang: str) -> str:
    """Lädt den Katalog. Fallback: en, dann Key selbst."""
    global _catalog, _lang
    lang = (lang or "en").lower()
    if lang not in available_languages():
        lang = "en"
    _lang = lang
    _catalog = _load_catalog(lang)
    if lang != "en":
        # fehlende Keys aus EN auffüllen
        base = _load_catalog("en")
        for k, v in base.items():
            _catalog.setdefault(k, v)
    return _lang


def get_language() -> str:
    return _lang


def tr(key: str, **kwargs: Any) -> str:
    """Übersetzt einen Message-Key; optionale .format(**kwargs)."""
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
