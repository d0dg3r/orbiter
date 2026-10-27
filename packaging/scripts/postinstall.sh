#!/bin/sh
# Nach Installation von Orbiter (deb/rpm/arch)
set -e

echo "Orbiter: Post-Install…"

# udev-Regeln neu laden (uinput)
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger --name-match=uinput 2>/dev/null || true
fi

# spacenavd stoppen — konkurriert um die SpaceMouse
if command -v systemctl >/dev/null 2>&1; then
    systemctl disable --now spacenavd 2>/dev/null || true
fi
if command -v pkill >/dev/null 2>&1; then
    pkill -x spacenavd 2>/dev/null || true
fi

echo ""
echo "Nächste Schritte:"
echo "  1. User der Gruppe «input» hinzufügen (für /dev/uinput), dann neu anmelden:"
echo "       sudo usermod -aG input \"\$USER\""
echo "  2. User-Dienst aktivieren:"
echo "       systemctl --user daemon-reload"
echo "       systemctl --user enable --now orbiter"
echo "  3. Status prüfen:  orbiter status"
echo ""
echo "Hinweis: spacenavd darf nicht parallel laufen (wird bei Install best-effort gestoppt)."
