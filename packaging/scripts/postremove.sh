#!/bin/sh
# Nach Entfernen von Orbiter
set -e

if command -v systemctl >/dev/null 2>&1; then
    # User-Units stoppen ist pro Session — best-effort Hinweis
    echo "Orbiter entfernt. Falls der User-Dienst noch lief:"
    echo "  systemctl --user disable --now orbiter"
fi
