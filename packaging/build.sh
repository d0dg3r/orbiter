#!/usr/bin/env bash
# Build Orbiter packages: .deb, .rpm, Arch .pkg.tar.zst
# Requires nfpm (https://nfpm.goreleaser.com/)
set -euo pipefail

export PATH="/usr/bin:/bin:/usr/local/bin:/usr/sbin:/sbin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STAGING="$SCRIPT_DIR/staging"
DIST="$ROOT/dist"
NFPM_CONFIG="$SCRIPT_DIR/nfpm.generated.yaml"

VERSION="${VERSION:-}"
if [[ -z "$VERSION" ]]; then
    VERSION="$(python3 -c "import tomllib; print(tomllib.load(open('$ROOT/pyproject.toml','rb'))['project']['version'])" 2>/dev/null \
        || python3 -c "import re; print(re.search(r'version\s*=\s*\"([^\"]+)\"', open('$ROOT/pyproject.toml').read()).group(1))")"
fi

echo "=== Orbiter Paket-Build v${VERSION} ==="

if ! command -v nfpm >/dev/null 2>&1; then
    echo "Fehler: «nfpm» fehlt. Installieren z. B.:"
    echo "  # Arch:   paru -S nfpm   bzw. aus releases.goreleaser.com"
    echo "  # Go:     go install github.com/goreleaser/nfpm/v2/cmd/nfpm@latest"
    echo "  # Deb:    siehe https://nfpm.goreleaser.com/install/"
    exit 1
fi

rm -rf "$STAGING"
mkdir -p \
    "$STAGING/usr/bin" \
    "$STAGING/usr/lib/orbiter" \
    "$STAGING/usr/lib/systemd/user" \
    "$STAGING/usr/share/applications" \
    "$STAGING/usr/share/icons/hicolor/scalable/apps" \
    "$STAGING/usr/lib/udev/rules.d" \
    "$DIST"

# Python package to /usr/lib/orbiter (distro-neutral, no site-packages)
rsync -a --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.pyo' \
    "$ROOT/orbiter/" "$STAGING/usr/lib/orbiter/orbiter/"

# CLI wrapper: PyQt6/evdev from distro packages, code from /usr/lib/orbiter
cat > "$STAGING/usr/bin/orbiter" << 'EOF'
#!/usr/bin/python3
"""Orbiter system entrypoint (distro package)."""
import sys
sys.path.insert(0, "/usr/lib/orbiter")
from orbiter.cli import main
if __name__ == "__main__":
    main()
EOF
chmod 755 "$STAGING/usr/bin/orbiter"

cp "$ROOT/data/orbiter.service" "$STAGING/usr/lib/systemd/user/orbiter.service"
cp "$ROOT/data/orbiter-tray.service" "$STAGING/usr/lib/systemd/user/orbiter-tray.service"
cp "$ROOT/data/orbiter.desktop" "$STAGING/usr/share/applications/orbiter.desktop"
cp "$ROOT/data/icons/orbiter.svg" "$STAGING/usr/share/icons/hicolor/scalable/apps/orbiter.svg"
cp "$ROOT/data/udev/99-orbiter-uinput.rules" "$STAGING/usr/lib/udev/rules.d/99-orbiter-uinput.rules"

# Inject version into nfpm spec (nfpm does not expand ${VERSION} itself)
sed "s/\${VERSION}/${VERSION}/g" "$SCRIPT_DIR/nfpm.yaml" > "$NFPM_CONFIG"

# Relative paths in nfpm.yaml are from repo root
cd "$ROOT"

for fmt in deb rpm archlinux; do
    echo "[…] baue $fmt …"
    nfpm package -f "$NFPM_CONFIG" -p "$fmt" -t "$DIST"
done

rm -f "$NFPM_CONFIG"

echo ""
echo "=== Fertig ==="
ls -lh "$DIST"/orbiter*
echo ""
echo "Install-Beispiele:"
echo "  Debian/Ubuntu:  sudo apt install ./dist/orbiter_${VERSION}*.deb"
echo "  Fedora/RHEL:    sudo dnf install ./dist/orbiter-${VERSION}*.rpm"
echo "  Arch:           sudo pacman -U ./dist/orbiter-${VERSION}*.pkg.tar.zst"
