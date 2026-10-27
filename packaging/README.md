# Orbiter — Distro-Pakete

Baut Installationspakete für Debian/Ubuntu (`.deb`), Fedora/RHEL (`.rpm`) und Arch Linux (`.pkg.tar.zst`). Laufzeit-Abhängigkeiten (Python, PyQt6, evdev, libnotify) kommen aus den Distro-Repos und werden vom Paketmanager mitinstalliert.

## Voraussetzung

[`nfpm`](https://nfpm.goreleaser.com/install/) muss im `PATH` liegen, z. B.:

```bash
go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest
# oder Binary von https://github.com/goreleaser/nfpm/releases
```

Zusätzlich: `rsync`, `python3`.

## Bauen

```bash
cd /pfad/zu/orbiter
./packaging/build.sh
# optional: VERSION=0.2.0 ./packaging/build.sh
```

Artefakte landen in `dist/`.

## GitHub Release (einmal lokal bauen)

Pakete werden **nur lokal** mit nfpm gebaut und als Release-Assets hochgeladen — kein zweites CI-Build:

```bash
./packaging/release.sh              # Version aus pyproject.toml
VERSION=0.2.0 ./packaging/release.sh
./packaging/release.sh --dry-run    # nur bauen, kein Upload
```

Voraussetzung: `gh` eingeloggt, Remote `github` → `d0dg3r/orbiter`. Skript setzt Tag `vX.Y.Z`, pusht ihn und führt `gh release create` (bzw. `upload --clobber`) aus.

## Installieren

```bash
# Debian / Ubuntu
sudo apt install ./dist/orbiter_*.deb

# Fedora / RHEL
sudo dnf install ./dist/orbiter-*.rpm

# Arch Linux
sudo pacman -U ./dist/orbiter-*-x86_64.pkg.tar.zst
```

Danach (einmalig pro User):

```bash
sudo usermod -aG input "$USER"   # danach neu anmelden
systemctl --user daemon-reload
systemctl --user enable --now orbiter
orbiter status
```

## Abhängigkeiten (deklariert im Paket)

| | Debian/Ubuntu | Fedora/RHEL | Arch |
|---|---|---|---|
| Interpreter | `python3` | `python3` | `python` |
| GUI | `python3-pyqt6` | `python3-pyqt6` | `python-pyqt6` |
| HID | `python3-evdev` | `python3-evdev` | `python-evdev` |
| Notify | `libnotify-bin` | `libnotify` | `libnotify` |

Empfohlen (X11-Auto-Profile): `xdotool`, `xprop` / `xorg-xprop`.

**Konflikt:** Paket deklariert `Conflicts` gegen `spacenavd`. Postinstall stoppt `spacenavd` best-effort. Läuft er trotzdem, startet der Orbiter-Daemon nicht (klare Fehlermeldung).

## Layout im System

| Pfad | Inhalt |
|---|---|
| `/usr/bin/orbiter` | CLI/GUI-Entrypoint |
| `/usr/lib/orbiter/` | Python-Package |
| `/usr/lib/systemd/user/orbiter.service` | User-Dienst |
| `/usr/share/applications/orbiter.desktop` | Desktop-Eintrag |
| `/usr/share/icons/hicolor/scalable/apps/orbiter.svg` | Icon |
| `/usr/lib/udev/rules.d/99-orbiter-uinput.rules` | uinput-Rechte (Gruppe `input`) |
