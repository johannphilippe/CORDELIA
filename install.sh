#!/usr/bin/env bash
# CORDELIA install script — macOS and Linux
set -e

VENV=".venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== CORDELIA installer ==="
echo

# ── helpers ───────────────────────────────────────────────────────────────────
need() { command -v "$1" >/dev/null 2>&1; }

python_ok() {
    local py="${1:-python3}"
    if need "$py"; then
        local ver
        ver=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        local major="${ver%%.*}" minor="${ver##*.}"
        [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]
    else
        return 1
    fi
}

# ── macOS ──────────────────────────────────────────────────────────────────────
install_macos() {
    echo "Platform: macOS"

    if ! need brew; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
    fi
    echo "[ok] Homebrew"

    if need csound; then
        echo "[ok] Csound already installed"
    else
        echo "Installing Csound..."
        brew install csound
    fi

    if brew list portaudio &>/dev/null; then
        echo "[ok] PortAudio already installed"
    else
        echo "Installing PortAudio..."
        brew install portaudio
    fi

    if python_ok python3; then
        echo "[ok] Python $(python3 --version)"
    else
        echo "Installing Python 3.11..."
        brew install python@3.11
    fi

    PYTHON=python3
}

# ── Linux (Debian/Ubuntu) ──────────────────────────────────────────────────────
install_linux() {
    echo "Platform: Linux"

    if ! need apt-get; then
        echo "[!] This script supports Debian/Ubuntu (apt). Install Csound manually for your distro."
        echo "    See: https://csound.com/download"
        exit 1
    fi

    local pkgs=()

    echo "Checking for Csound..."
    if need csound; then
        echo "[ok] Csound already installed"
    else
        pkgs+=(csound)
    fi

    echo "Checking for PortAudio..."
    # portaudio19-dev provides the shared library sounddevice links against
    if dpkg -s portaudio19-dev &>/dev/null 2>&1; then
        echo "[ok] PortAudio already installed"
    else
        pkgs+=(portaudio19-dev)
    fi

    echo "Checking for Python 3.11+..."
    if python_ok python3; then
        echo "[ok] Python $(python3 --version)"
    else
        echo "Python 3.11+ not found, will install..."
        pkgs+=(python3.11 python3.11-venv)
    fi

    # python3-full bundles ensurepip, which is required to put pip inside a venv.
    # Ubuntu ships Python without it by default — always ensure it is present.
    if ! dpkg -s python3-full &>/dev/null 2>&1; then
        pkgs+=(python3-full python3-venv)
    fi

    if [ ${#pkgs[@]} -gt 0 ]; then
        echo "Installing via apt: ${pkgs[*]}"
        sudo apt-get update -qq
        sudo apt-get install -y "${pkgs[@]}"
    fi

    PYTHON=python3
}

# ── detect platform ────────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

case "$(uname -s)" in
    Darwin) install_macos ;;
    Linux)  install_linux ;;
    *)
        echo "[!] Unsupported platform: $(uname -s)"
        echo "    Install Csound manually: https://csound.com/download"
        exit 1
        ;;
esac

# ── virtual environment ────────────────────────────────────────────────────────
echo
# Recreate the venv if it exists but pip is missing inside it (broken venv)
if [ -d "$VENV" ] && [ ! -f "$VENV/bin/pip" ]; then
    echo "[!] Existing .venv has no pip — recreating it..."
    rm -rf "$VENV"
fi

if [ -d "$VENV" ]; then
    echo "[ok] Virtual environment already exists at $VENV"
else
    echo "Creating virtual environment at $VENV ..."
    "$PYTHON" -m venv "$VENV"
    # Verify pip landed inside the venv
    if [ ! -f "$VENV/bin/pip" ]; then
        echo "[!] pip was not installed inside the venv."
        echo "    Trying ensurepip..."
        "$PYTHON" -m ensurepip --upgrade
        "$VENV/bin/python" -m ensurepip --upgrade
    fi
fi

# ── Python deps ────────────────────────────────────────────────────────────────
echo "Installing Python dependencies into $VENV ..."
"$VENV/bin/pip" install --upgrade pip --quiet
"$VENV/bin/pip" install -r requirements.txt

# ── run helper ────────────────────────────────────────────────────────────────
cat > run.sh << 'RUN'
#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")"
exec .venv/bin/python cordelia/cordelia.py "$@"
RUN
chmod +x run.sh

echo
echo "=== Done ==="
echo
echo "Run CORDELIA with:"
echo "  bash run.sh"
echo
echo "Or activate the environment manually and use Python directly:"
echo "  source .venv/bin/activate"
echo "  python cordelia/cordelia.py"
