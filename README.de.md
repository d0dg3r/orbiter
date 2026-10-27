# Orbiter

**Nativer Linux- & Wayland-Treiber + GUI für 3Dconnexion SpaceMouse-Geräte**

[Read in English](README.md) · Lizenz: [MIT](LICENSE) · [Mitmachen](CONTRIBUTING.md)

Orbiter macht aus 3Dconnexion-6DoF-Geräten (SpaceExplorer, SpaceNavigator, SpaceMouse Pro, SpacePilot, …) unter Linux (Wayland & X11) eine flüssige, stark anpassbare 2D-Präzisionsmaus, Navigationssteuerung und Makro-Pad.

![Orbiter Icon](data/icons/orbiter.svg)

---

## Funktionen

- **Joystick-artiger Zeiger:** 60-Hz-Ticker mit einstellbarer Geschwindigkeitskurve
- **2D-Präzisionsmodus:** Pitch/Roll/Tilt sperren für planares Gleiten
- **Anti-Ghost-Scroll:** Scroll-Sperre beim Bewegen + Cooldown; Scrollen per Twist
- **Profile:** anlegen, duplizieren, umbenennen, löschen; Wechsel per GUI, Tray oder Hardware
- **Auto-Profile:** Wechsel nach aktivem Fenster (Hyprland / X11)
- **Dunkle PyQt6-GUI** mit Live-Hardware-Monitor
- **Live-Config-Reload** ohne Daemon-Neustart
- **Config Export / Import** — JSON-Backup über Einstellungen oder `orbiter config`
- **Tray beim Login** — `orbiter-tray.service` (Daemon bleibt `orbiter.service`)
- **DE / EN Oberfläche** — Sprache folgt dem System oder Einstellungen → Sprache

---

## Voraussetzungen

- Linux mit `uinput` (User idealerweise in der Gruppe `input`)
- Python 3.10+
- PyQt6, python-evdev, libnotify (`notify-send`)
- **spacenavd muss deaktiviert sein** — Konflikt um dasselbe HID-Gerät

---

## Installation

### Distro-Pakete (empfohlen)

```bash
./packaging/build.sh   # benötigt nfpm

# Debian/Ubuntu
sudo apt install ./dist/orbiter_*.deb

# Fedora/RHEL
sudo dnf install ./dist/orbiter-*.rpm

# Arch
sudo pacman -U ./dist/orbiter-*-x86_64.pkg.tar.zst

sudo usermod -aG input "$USER"   # danach neu anmelden
systemctl --user daemon-reload
systemctl --user enable --now orbiter
systemctl --user enable --now orbiter-tray
```

Details: [packaging/README.md](packaging/README.md)

GitHub-Release aus einem lokalen Build:

```bash
./packaging/release.sh
```

### Entwickler-Install

```bash
./install.sh
```

---

## Nutzung

```bash
orbiter                 # GUI + Tray
orbiter --tray          # nur Tray (auch via orbiter-tray.service)
orbiter status          # Verbindung, Profil, spacenavd-Konflikt
orbiter profile next    # Profil wechseln
orbiter 2d              # 2D-Modus umschalten
orbiter config export [pfad]   # Default: ~/orbiter-config-YYYYMMDD.json
orbiter config import <pfad>   # ersetzt Config; Daemon bekommt RELOAD
orbiter restart         # User-Dienst neu starten
```

Konfiguration: `~/.config/orbiter/config.json`  
Export/Import auch unter **Einstellungen → Konfigurations-Backup**.

---

## Mitmachen

Beiträge sind willkommen — Code, Doku, Übersetzungen, Packaging, Tests mit weiteren SpaceMouse-Modellen. Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Lizenz

[MIT](LICENSE) © 2026 devops-geek / Joe
