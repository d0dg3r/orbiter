# Orbiter

**Native Linux & Wayland driver + GUI for 3Dconnexion SpaceMouse devices**

[Deutsch lesen](README.de.md) · License: [MIT](LICENSE) · [Contributing](CONTRIBUTING.md)

Orbiter turns 3Dconnexion 6DoF devices (SpaceExplorer, SpaceNavigator, SpaceMouse Pro, SpacePilot, …) into a fluid, highly customizable 2D precision mouse, navigation controller, and macro pad under Linux (Wayland & X11).

![Orbiter Icon](data/icons/orbiter.svg)

---

## Features

- **Fluid joystick-style pointer:** 60 Hz ticker with customizable velocity curve
- **2D precision mode:** lock out pitch/roll/tilt for planar desktop gliding
- **Anti-ghost scroll:** scroll lock while moving + cooldown; twist-to-scroll
- **Profiles:** create, duplicate, rename, delete; switch via GUI, tray, or hardware
- **Auto profiles:** switch by active window (Hyprland / X11)
- **Dark PyQt6 GUI** with live hardware monitor
- **Live config reload** without restarting the daemon
- **Config export / import** — JSON backup via Settings or `orbiter config`
- **Tray at login** — `orbiter-tray.service` (daemon stays `orbiter.service`)
- **DE / EN UI** — language follows the system or Settings → Language

---

## Requirements

- Linux with `uinput` (user in group `input` recommended)
- Python 3.10+
- PyQt6, python-evdev, libnotify (`notify-send`)
- **spacenavd must be disabled** — it conflicts with Orbiter on the same HID device

---

## Install

### Distro packages (recommended)

```bash
./packaging/build.sh   # needs nfpm

# Debian/Ubuntu
sudo apt install ./dist/orbiter_*.deb

# Fedora/RHEL
sudo dnf install ./dist/orbiter-*.rpm

# Arch
sudo pacman -U ./dist/orbiter-*-x86_64.pkg.tar.zst

sudo usermod -aG input "$USER"   # then re-login
systemctl --user daemon-reload
systemctl --user enable --now orbiter
systemctl --user enable --now orbiter-tray
```

Details: [packaging/README.md](packaging/README.md)

Publish a GitHub Release from a single local build (notes from [CHANGELOG.md](CHANGELOG.md); older releases are removed so only the current one stays):

```bash
# bump pyproject.toml + add ## [X.Y.Z] in CHANGELOG.md, commit, then:
./packaging/release.sh
```

### Developer install

```bash
./install.sh
```

---

## Usage

```bash
orbiter                 # GUI + tray
orbiter --tray          # tray only (also started by orbiter-tray.service)
orbiter status          # connection, profile, spacenavd conflict
orbiter profile next    # switch profile
orbiter 2d              # toggle 2D mode
orbiter config export [path]   # default: ~/orbiter-config-YYYYMMDD.json
orbiter config import <path>   # replaces config; daemon gets RELOAD
orbiter restart         # restart user service
```

Config: `~/.config/orbiter/config.json`  
Export/import also under **Settings → Configuration backup**.

---

## Contributing

Contributions are welcome — code, docs, translations, packaging, testing on more SpaceMouse models. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

[MIT](LICENSE) © 2026 devops-geek / Joe
