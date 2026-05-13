#!/usr/bin/env bash
# Build the Cordelia VS Code extension as a .vsix file.
# Requires: Node.js (18+) and npm
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v npm >/dev/null 2>&1; then
    echo "[!] npm not found."
    echo "    Install Node.js from https://nodejs.org and re-run this script."
    exit 1
fi

echo "Installing dev dependencies..."
npm install --save-dev @vscode/vsce --silent

# Node.js <20 is missing the File global that undici/vsce expects.
# Polyfill it from the built-in 'buffer' module if needed.
POLYFILL=""
node -e "if(!globalThis.File){process.exit(1)}" 2>/dev/null || {
    POLYFILL_FILE="$(mktemp /tmp/file-polyfill-XXXX.js)"
    echo "const { File } = require('buffer'); globalThis.File = File;" > "$POLYFILL_FILE"
    POLYFILL="--require $POLYFILL_FILE"
    echo "[info] Node.js <20 detected — applying File polyfill"
}

echo "Packaging extension..."
NODE_OPTIONS="$POLYFILL" npx vsce package --no-dependencies

[ -n "$POLYFILL_FILE" ] && rm -f "$POLYFILL_FILE"

vsix=$(ls cordelia-*.vsix 2>/dev/null | grep -v 'cordelia-latest' | tail -1)
cp "$vsix" cordelia-latest.vsix

echo
echo "=== Done ==="
echo "Package: $vsix"
echo "Latest:  cordelia-latest.vsix (tracked in git)"
echo
echo "Install in VS Code:"
echo "  code --install-extension cordelia-latest.vsix"
echo
echo "Or: Extensions panel → ··· → Install from VSIX..."
