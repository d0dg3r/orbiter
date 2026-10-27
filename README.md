# 🛸 Orbiter

**Native Linux & Wayland Driver + GUI Controller for 3Dconnexion SpaceMouse Devices**

Orbiter turns 3Dconnexion 6DoF devices (SpaceExplorer, SpaceNavigator, SpaceMouse Pro, SpacePilot) into a fluid, highly customizable 2D precision mouse, navigation controller, and macro pad under Linux (Wayland & X11).

![Orbiter Icon](data/icons/orbiter.svg)

---

## ✨ Features

- **Fluid Joystick-Style Pointer Translation:** 60 Hz ticker with customizable velocity curve. Push slightly for precision, push harder for speed.
- **2D-Precision Mode:** Lock out pitch/roll/tilt with a single button press for 100% planar gliding on the desktop.
- **Anti-Ghost Scroll Protection:**
  - 100% scroll lockout while moving the pointer.
  - 150 ms cooldown prevents accidental scrolling when releasing the cap.
  - Twist-based scrolling (turn the cap like a knob for buttery smooth page scrolling).
- **Profile Management:**
  - Create, duplicate, rename, and delete profiles (e.g., `Standard`, `CAD / 3D`, `Browser / Medien`).
  - Switch profiles via GUI toolbar, system tray menu, or dedicated hardware buttons (`next_profile`, `prev_profile`, `profile:<name>`).
  - Native desktop notifications (`notify-send`) when switching profiles.
- **Modern Dark GUI (PyQt6):**
  - **Dropdown Button Editor:** Intuitive dropdown selectors for mouse buttons, internal functions & profiles, individual keys, shortcuts with modifier checkboxes, and Hyprland presets.
  - **Sensitivity Sliders:** Live adjustment of pointer speed, deadzones, and scroll speed per profile.
  - **Live Hardware Monitor:** Real-time 6-axis visualizer and button press tester.
- **Live Config Reload:** Changes in the GUI or `~/.config/orbiter/config.json` take effect immediately without restarting the daemon.
- **Hyprland & Wayland Native:** Full integration with Hyprland workspaces and Wayland compositors via kernel `uinput`.

---

## 🚀 Installation

Run the automated installer:

```bash
cd ~/Development/orbiter
./install.sh
```

This will:
1. Symlink `orbiter` into `~/.local/bin/orbiter`.
2. Install the desktop entry for Rofi / App-Launcher.
3. Install and start the background systemd user service (`orbiter.service`).

---

## 🛠️ Usage

### Open Settings GUI
Search for **Orbiter** in your app launcher (Rofi / Super+D) or run:
```bash
orbiter
```

### CLI Commands
```bash
orbiter status                       # Check connection, active profile, and mode
orbiter profile                      # List all available profiles and active profile
orbiter profile <name|next|prev>     # Switch to profile (e.g. 'CAD / 3D', 'next', 'prev')
orbiter 2d                           # Toggle 2D precision mode
orbiter reload                       # Reload config from disk
orbiter restart                      # Restart systemd background service
orbiter daemon                       # Run daemon interactively in foreground
```

---

## 📁 Configuration

Configuration is stored in human-readable JSON:
`~/.config/orbiter/config.json`

---

## 📜 License
MIT License
