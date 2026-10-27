#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installiere Orbiter ==="

# 1. Ensure directories exist
mkdir -p "$BIN_DIR" "$APPS_DIR" "$ICONS_DIR" "$SYSTEMD_USER_DIR"

# 2. CLI Symlink
ln -sf "$SCRIPT_DIR/bin/orbiter" "$BIN_DIR/orbiter"
echo "[✓] Symlink erstellt: $BIN_DIR/orbiter"

# 3. Copy icon
cp "$SCRIPT_DIR/data/icons/orbiter.svg" "$ICONS_DIR/orbiter.svg"
echo "[✓] Icon installiert in $ICONS_DIR"

# 4. Desktop entry
cp "$SCRIPT_DIR/data/orbiter.desktop" "$APPS_DIR/orbiter.desktop"
update-desktop-database "$APPS_DIR" 2>/dev/null || true
echo "[✓] Desktop-Eintrag installiert (Rofi / App-Starter)"

# 5. Systemd user services (dev: ExecStart points at local symlink)
cp "$SCRIPT_DIR/data/orbiter.service" "$SYSTEMD_USER_DIR/orbiter.service"
cp "$SCRIPT_DIR/data/orbiter-tray.service" "$SYSTEMD_USER_DIR/orbiter-tray.service"
# Package units use /usr/bin/orbiter; dev install uses ~/.local/bin
sed -i "s|ExecStart=/usr/bin/orbiter|ExecStart=$BIN_DIR/orbiter|" \
    "$SYSTEMD_USER_DIR/orbiter.service" \
    "$SYSTEMD_USER_DIR/orbiter-tray.service"
systemctl --user daemon-reload

# Stop and disable legacy provisional service if present
systemctl --user stop spacenav-mouse 2>/dev/null || true
systemctl --user disable spacenav-mouse 2>/dev/null || true

# spacenavd contends for the same HID device — must be off or Orbiter cannot work
if systemctl is-active --quiet spacenavd 2>/dev/null \
    || systemctl --user is-active --quiet spacenavd 2>/dev/null \
    || pgrep -x spacenavd >/dev/null 2>&1; then
    echo "[!] spacenavd erkannt — stoppe und deaktiviere (Konflikt mit Orbiter)…"
    sudo systemctl disable --now spacenavd 2>/dev/null || true
    systemctl --user disable --now spacenavd 2>/dev/null || true
    sudo pkill -x spacenavd 2>/dev/null || true
    if pgrep -x spacenavd >/dev/null 2>&1; then
        echo "[✗] spacenavd läuft noch. Bitte manuell: sudo systemctl disable --now spacenavd"
        exit 1
    fi
    echo "[✓] spacenavd gestoppt"
fi

# Enable and start daemon + tray
systemctl --user enable --now orbiter
systemctl --user enable --now orbiter-tray
echo "[✓] Systemd-Dienste 'orbiter' und 'orbiter-tray' aktiviert und gestartet"

echo ""
echo "=== Installation erfolgreich abgeschlossen! ==="
echo "Du kannst Orbiter jetzt verwenden:"
echo " - App-Starter (Rofi): Suche nach 'Orbiter'"
echo " - Terminal: 'orbiter' (öffnet die GUI)"
echo " - Tray startet beim Login (orbiter-tray.service)"
echo " - Dienst-Status: 'orbiter status'"
