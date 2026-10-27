#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installiere Orbiter ==="

# 1. Verzeichnisse sicherstellen
mkdir -p "$BIN_DIR" "$APPS_DIR" "$ICONS_DIR" "$SYSTEMD_USER_DIR"

# 2. CLI Symlink
ln -sf "$SCRIPT_DIR/bin/orbiter" "$BIN_DIR/orbiter"
echo "[✓] Symlink erstellt: $BIN_DIR/orbiter"

# 3. Icon kopieren
cp "$SCRIPT_DIR/data/icons/orbiter.svg" "$ICONS_DIR/orbiter.svg"
echo "[✓] Icon installiert in $ICONS_DIR"

# 4. Desktop-Eintrag
cp "$SCRIPT_DIR/data/orbiter.desktop" "$APPS_DIR/orbiter.desktop"
update-desktop-database "$APPS_DIR" 2>/dev/null || true
echo "[✓] Desktop-Eintrag installiert (Rofi / App-Starter)"

# 5. Systemd User Service
cp "$SCRIPT_DIR/data/orbiter.service" "$SYSTEMD_USER_DIR/orbiter.service"
systemctl --user daemon-reload

# Alten provisorischen Dienst stoppen und deaktivieren falls vorhanden
systemctl --user stop spacenav-mouse 2>/dev/null || true
systemctl --user disable spacenav-mouse 2>/dev/null || true

# Neuen Orbiter Dienst aktivieren und starten
systemctl --user enable --now orbiter
echo "[✓] Systemd-Dienst 'orbiter.service' aktiviert und gestartet"

echo ""
echo "=== Installation erfolgreich abgeschlossen! ==="
echo "Du kannst Orbiter jetzt verwenden:"
echo " - App-Starter (Rofi): Suche nach 'Orbiter'"
echo " - Terminal: 'orbiter' (öffnet die GUI)"
echo " - Dienst-Status: 'orbiter status'"
