# Contributing to Orbiter / Mitmachen bei Orbiter

**Everyone is welcome.** Whether you fix a typo, improve the driver, add a SpaceMouse layout, translate a string, or package for another distro — thank you.

**Jede:r ist willkommen.** Tippsfehler, Treiber-Fixes, neue SpaceMouse-Layouts, Übersetzungen oder Pakete für weitere Distros — danke.

---

## English

### How to contribute

1. Fork the repo on [GitHub](https://github.com/d0dg3r/orbiter) (public) or ask for access on the internal Forgejo mirror.
2. Create a branch: `git checkout -b feature/my-change`
3. Make focused commits with a clear message (why > what).
4. Open a Pull Request against `main`. Describe the change and how you tested it.

### Development setup

```bash
git clone https://github.com/d0dg3r/orbiter.git
cd orbiter
./install.sh          # or: pip install -e .  + systemctl --user …
orbiter daemon        # foreground driver for debugging
orbiter               # GUI
```

**Important:** disable `spacenavd` first (`sudo systemctl disable --now spacenavd`).

### Translations (DE / EN)

UI strings live in:

- `orbiter/locales/en.json`
- `orbiter/locales/de.json`

Use `tr("key")` / `tr("key", name=…)` from `orbiter.i18n`. Keep keys in sync between both files. New keys → add to **both** locales in the same PR.

Docs: keep `README.md` (EN) and `README.de.md` (DE) aligned when you change install/usage.

### Code style

- Python 3.10+, readable, minimal comments (explain “why”, not the obvious)
- No secrets in commits
- Prefer Swiss German orthography in German user-facing text (`ss` not `ß`, «…»)

### Reporting issues

Include: distro, Orbiter version, SpaceMouse model, whether `spacenavd` was running, and `orbiter status` output.

---

## Deutsch

### So trägst du bei

1. Fork auf [GitHub](https://github.com/d0dg3r/orbiter) (öffentlich) oder Zugriff auf den internen Forgejo-Spiegel anfragen.
2. Branch: `git checkout -b feature/meine-aenderung`
3. Fokussierte Commits mit klarer Message (Warum > Was).
4. Pull Request gegen `main`. Änderung und Test kurz beschreiben.

### Dev-Setup

```bash
git clone https://github.com/d0dg3r/orbiter.git
cd orbiter
./install.sh
orbiter daemon
orbiter
```

**Wichtig:** `spacenavd` zuerst deaktivieren.

### Übersetzungen

Strings: `orbiter/locales/{en,de}.json` — Keys in beiden Dateien pflegen. Doku: `README.md` und `README.de.md` zusammen halten.

### Issues

Bitte mitliefern: Distro, Orbiter-Version, SpaceMouse-Modell, ob `spacenavd` lief, Ausgabe von `orbiter status`.

---

## Code of conduct (short)

Be respectful. No harassment, no gatekeeping. Assume good intent. Maintainers may moderate discussion that blocks collaboration.
