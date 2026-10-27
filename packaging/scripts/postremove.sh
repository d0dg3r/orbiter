#!/bin/sh
# After Orbiter package removal
set -e

if command -v systemctl >/dev/null 2>&1; then
    # Stopping user units is per-session — best-effort hint only
    echo "Orbiter entfernt. Falls der User-Dienst noch lief:"
    echo "  systemctl --user disable --now orbiter"
fi
