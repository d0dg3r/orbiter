# Changelog

All notable changes to Orbiter are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Release notes on GitHub are taken from the matching version section below.
Only the latest release is kept published; older GitHub releases are removed by `packaging/release.sh`.

## [0.1.3] - 2026-10-27

### Added

- Separate **Sensitivity** and **Settings** tabs (language + config backup stay under Settings)
- Harmonized tab page spacing SoT (`apply_tab_page_layout` / GroupBox padding) across all tabs

### Changed

- Window assignment tab title no longer includes «(Auto-Switch)»
- Live hardware tester: axis labels as name + hint, clearer button status layout
- Settings group boxes: compact but not cramped vertical rhythm

## [0.1.2] - 2026-10-27

### Changed

- Packaging rebuild for the Sensitivity / Settings tab split (see 0.1.3 for full UI notes)

## [0.1.1] - 2026-10-27

### Added

- Config export / import in Settings
- `orbiter-tray` systemd user unit for login autostart
- Copyright footer and GitHub link in the GUI

### Changed

- Source comments standardized to English

## [0.1.0] - 2026-10-27

### Added

- Initial public release: SpaceMouse daemon, PyQt6 GUI, profiles, button mapping, window rules
- Distro packages (deb / rpm / Arch) via nfpm
- DE/EN UI language (system default or manual)
- Conflict guard against `spacenavd`
