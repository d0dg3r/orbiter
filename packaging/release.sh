#!/usr/bin/env bash
# Build Orbiter packages once locally and publish as the sole GitHub release.
# Usage:
#   ./packaging/release.sh              # version from pyproject.toml
#   VERSION=0.2.0 ./packaging/release.sh
#   ./packaging/release.sh --dry-run    # build only, no upload
#
# Requires a matching "## [X.Y.Z]" section in CHANGELOG.md (release notes SoT).
# Deletes every other GitHub release (+ tags) so only the current one remains.
set -euo pipefail

export PATH="/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin:${HOME}/go/bin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST="$ROOT/dist"
CHANGELOG="$ROOT/CHANGELOG.md"
GH_REPO="${GH_REPO:-d0dg3r/orbiter}"
DRY_RUN=0

for arg in "$@"; do
    case "$arg" in
        --dry-run|-n) DRY_RUN=1 ;;
        -h|--help)
            echo "Usage: $0 [--dry-run]   VERSION=x.y.z optional"
            exit 0
            ;;
    esac
done

cd "$ROOT"

VERSION="${VERSION:-}"
if [[ -z "$VERSION" ]]; then
    VERSION="$(python3 -c "import re; print(re.search(r'version\s*=\s*\"([^\"]+)\"', open('pyproject.toml').read()).group(1))")"
fi
VERSION="${VERSION#v}"
TAG="v${VERSION}"

echo "=== Orbiter Release ${TAG} → ${GH_REPO} ==="

if ! command -v gh >/dev/null 2>&1; then
    echo "Fehler: «gh» (GitHub CLI) fehlt."
    exit 1
fi

if [[ ! -f "$CHANGELOG" ]]; then
    echo "Fehler: CHANGELOG.md fehlt — Release-Notes sind Pflicht."
    exit 1
fi

NOTES="$(mktemp)"
trap 'rm -f "$NOTES"' EXIT

python3 - "$CHANGELOG" "$VERSION" "$NOTES" <<'PY'
import re
import sys
from pathlib import Path

changelog, version, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
text = Path(changelog).read_text(encoding="utf-8")
pattern = rf"(?ms)^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)"
match = re.search(pattern, text)
if not match or not match.group(1).strip():
    print(
        f"Fehler: keine Release-Notes für {version} in CHANGELOG.md "
        f"(erwartet: ## [{version}] - …).",
        file=sys.stderr,
    )
    sys.exit(1)

body = match.group(1).strip()
notes = f"""## Orbiter v{version}

{body}

### Install

```bash
# Debian / Ubuntu
sudo apt install ./orbiter_*.deb

# Fedora / RHEL
sudo dnf install ./orbiter-*.rpm

# Arch
sudo pacman -U ./orbiter-*-x86_64.pkg.tar.zst
```

Then: `sudo usermod -aG input "$USER"` (re-login) and `systemctl --user enable --now orbiter`.

**Note:** disable `spacenavd` first — it conflicts with Orbiter.
"""
Path(out_path).write_text(notes, encoding="utf-8")
print(f"[✓] Release-Notes aus CHANGELOG.md [{version}]")
PY

"$SCRIPT_DIR/build.sh"

shopt -s nullglob
ASSETS=(
    "$DIST"/orbiter_"${VERSION}"*.deb
    "$DIST"/orbiter-"${VERSION}"*.rpm
    "$DIST"/orbiter-"${VERSION}"*.pkg.tar.zst
)
if [[ ${#ASSETS[@]} -eq 0 ]]; then
    ASSETS=("$DIST"/orbiter_*.deb "$DIST"/orbiter-*.rpm "$DIST"/orbiter-*.pkg.tar.zst)
fi
REAL_ASSETS=()
for a in "${ASSETS[@]}"; do
    [[ -f "$a" ]] && REAL_ASSETS+=("$a")
done
if [[ ${#REAL_ASSETS[@]} -eq 0 ]]; then
    echo "Fehler: keine Pakete in dist/ gefunden."
    exit 1
fi

echo "Assets:"
printf '  - %s\n' "${REAL_ASSETS[@]}"

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] Skip tag/push/gh release. Would upload:"
    printf '  %s\n' "${REAL_ASSETS[@]}"
    echo "[dry-run] Notes preview:"
    cat "$NOTES"
    exit 0
fi

if ! git rev-parse "$TAG" >/dev/null 2>&1; then
    git tag -a "$TAG" -m "Orbiter ${TAG}"
    echo "[✓] Tag ${TAG} erstellt"
else
    echo "[…] Tag ${TAG} existiert schon"
fi

if git remote get-url github >/dev/null 2>&1; then
    git push github HEAD:main 2>/dev/null || true
    git push github "$TAG" 2>/dev/null || git push github "refs/tags/${TAG}"
    echo "[✓] Tag nach github gepusht"
else
    echo "[!] Remote «github» fehlt — Tag bitte manuell pushen"
fi

# Remove every other GitHub release so only the current one remains.
mapfile -t OLD_TAGS < <(gh release list --repo "$GH_REPO" --limit 100 --json tagName -q '.[].tagName' 2>/dev/null || true)
for old in "${OLD_TAGS[@]:-}"; do
    [[ -z "$old" || "$old" == "$TAG" ]] && continue
    echo "[…] Lösche altes Release ${old}"
    gh release delete "$old" --repo "$GH_REPO" --yes --cleanup-tag || true
done

if gh release view "$TAG" --repo "$GH_REPO" >/dev/null 2>&1; then
    echo "[…] Release ${TAG} existiert — Notes + Assets aktualisieren"
    gh release edit "$TAG" --repo "$GH_REPO" --title "Orbiter ${TAG}" --notes-file "$NOTES"
    gh release upload "$TAG" "${REAL_ASSETS[@]}" --repo "$GH_REPO" --clobber
else
    gh release create "$TAG" "${REAL_ASSETS[@]}" \
        --repo "$GH_REPO" \
        --title "Orbiter ${TAG}" \
        --notes-file "$NOTES"
fi

echo ""
echo "=== Release fertig (nur ${TAG}) ==="
echo "https://github.com/${GH_REPO}/releases/tag/${TAG}"
