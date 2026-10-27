#!/usr/bin/env bash
# Baut Orbiter-Pakete lokal (einmal) und veröffentlicht sie als GitHub-Release-Assets.
# Nutzung:
#   ./packaging/release.sh              # Version aus pyproject.toml
#   VERSION=0.2.0 ./packaging/release.sh
#   ./packaging/release.sh --dry-run    # nur bauen, kein Upload
set -euo pipefail

export PATH="/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin:${HOME}/go/bin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST="$ROOT/dist"
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
TAG="v${VERSION#v}"

echo "=== Orbiter Release ${TAG} → ${GH_REPO} ==="

if ! command -v gh >/dev/null 2>&1; then
    echo "Fehler: «gh» (GitHub CLI) fehlt."
    exit 1
fi

"$SCRIPT_DIR/build.sh"

shopt -s nullglob
ASSETS=(
    "$DIST"/orbiter_"${VERSION}"*.deb
    "$DIST"/orbiter-"${VERSION}"*.rpm
    "$DIST"/orbiter-"${VERSION}"*.pkg.tar.zst
)
# Fallback: alle orbiter-Artefakte in dist/
if [[ ${#ASSETS[@]} -eq 0 ]]; then
    ASSETS=("$DIST"/orbiter_*.deb "$DIST"/orbiter-*.rpm "$DIST"/orbiter-*.pkg.tar.zst)
fi
# Drop empty globs
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

NOTES="$(mktemp)"
trap 'rm -f "$NOTES"' EXIT
cat > "$NOTES" << EOF
## Orbiter ${TAG}

Linux packages built locally with nfpm (deb / rpm / Arch).

### Install

\`\`\`bash
# Debian / Ubuntu
sudo apt install ./orbiter_*.deb

# Fedora / RHEL
sudo dnf install ./orbiter-*.rpm

# Arch
sudo pacman -U ./orbiter-*-x86_64.pkg.tar.zst
\`\`\`

Then: \`sudo usermod -aG input "\$USER"\` (re-login) and \`systemctl --user enable --now orbiter\`.

**Note:** disable \`spacenavd\` first — it conflicts with Orbiter.
EOF

if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] Skip tag/push/gh release. Would upload:"
    printf '  %s\n' "${REAL_ASSETS[@]}"
    exit 0
fi

# Tag lokal + auf github Remote
if ! git rev-parse "$TAG" >/dev/null 2>&1; then
    git tag -a "$TAG" -m "Orbiter ${TAG}"
    echo "[✓] Tag ${TAG} erstellt"
else
    echo "[…] Tag ${TAG} existiert schon"
fi

if git remote get-url github >/dev/null 2>&1; then
    git push github "$TAG" 2>/dev/null || git push github "refs/tags/${TAG}"
    echo "[✓] Tag nach github gepusht"
else
    echo "[!] Remote «github» fehlt — Tag bitte manuell pushen"
fi

if gh release view "$TAG" --repo "$GH_REPO" >/dev/null 2>&1; then
    echo "[…] Release ${TAG} existiert — lade Assets neu hoch (--clobber)"
    gh release upload "$TAG" "${REAL_ASSETS[@]}" --repo "$GH_REPO" --clobber
else
    gh release create "$TAG" "${REAL_ASSETS[@]}" \
        --repo "$GH_REPO" \
        --title "Orbiter ${TAG}" \
        --notes-file "$NOTES"
fi

echo ""
echo "=== Release fertig ==="
echo "https://github.com/${GH_REPO}/releases/tag/${TAG}"
