# Installing CORDELIA

CORDELIA requires two things that cannot be installed with pip alone:

- **Csound 6.17+** — the audio engine (a native library)
- **Python 3.11+** — the runtime

Everything else is installed automatically.

---

## Option 1 — Automated script (recommended for beginners)

### macOS / Linux

```bash
bash install.sh
```

The script:
- Checks whether Csound and PortAudio are already installed before installing them
- Installs Csound and PortAudio via Homebrew (macOS) or apt (Ubuntu/Debian)
- Installs **Python 3.11 specifically** (not just any 3.11+) to ensure all dependency wheels are available
- Creates a virtual environment at `.venv/` (avoids system Python conflicts)
- Installs all Python dependencies into the venv
- Generates a `run.sh` launch script

After installation, start CORDELIA with:

```bash
bash run.sh
```

### Windows

Open PowerShell as a normal user and run:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

Requires **winget** (included in Windows 10 version 1709+ / Windows 11).

The script checks for existing Csound and Python installations before installing,
creates a `.venv\` virtual environment, and generates a `run.bat` launch script.

After installation:

```
run.bat
```

---

## Option 2 — pixi (Linux and macOS, one command)

[pixi](https://pixi.sh) manages Python, Csound, and all dependencies in a single step.

**Install pixi** (once):

```bash
curl -fsSL https://pixi.sh/install.sh | bash
# restart your terminal, or: source ~/.bashrc
```

**Install and run CORDELIA:**

```bash
cd CORDELIA
pixi install
pixi run cordelia
```

> Windows is not yet supported via this path because the Csound conda-forge package
> does not reliably support win-64. Use Option 1 or Option 3 on Windows.

---

## Option 3 — Manual (any platform)

### Step 1 — Install Csound

| Platform | Method |
|----------|--------|
| **Windows** | Download the `.exe` installer from [csound.com/download](https://csound.com/download) and run it. Tick "Add to PATH" if asked. |
| **macOS** | `brew install csound` (requires [Homebrew](https://brew.sh)), or download the `.pkg` from [csound.com/download](https://csound.com/download) |
| **Linux (Debian/Ubuntu)** | `sudo apt install csound portaudio19-dev` |
| **Linux (other)** | See [csound.com/download](https://csound.com/download) |

### Step 2 — Install Python 3.11+

| Platform | Method |
|----------|--------|
| **Windows / macOS** | Download from [python.org/downloads](https://www.python.org/downloads/). On Windows, tick "Add Python to PATH". |
| **Linux** | Usually pre-installed; otherwise `sudo apt install python3.11 python3-pip` |

### Step 3 — Create a virtual environment and install dependencies

```bash
python3 -m venv .venv          # create the environment (once)
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

> Recent Ubuntu/Debian systems enforce PEP 668 and block system-wide pip installs.
> Using a venv (as above) is the correct fix.

### Step 4 — Run

```bash
.venv/bin/python cordelia/cordelia.py   # macOS / Linux
.venv\Scripts\python cordelia\cordelia.py  # Windows
```

---

## Option 4 — conda / Miniforge

Useful if you already use Conda or Miniforge.

Install [Miniforge](https://github.com/conda-forge/miniforge/releases/latest) if you don't have it, then:

```bash
conda env create -f environment.yml
conda activate cordelia
python cordelia/cordelia.py
```

> On Windows, Csound may not be available through conda-forge.
> In that case install Csound manually (Step 1 of Option 3) before activating the environment.

---

## Optional — LilyPond (notation output only)

`abjad` is installed as part of the Python dependencies and is used internally
for rhythm parsing. LilyPond is only needed if you want to **render notation scores**
to PDF or PNG. It is not required for live coding.

| Platform | Install |
|----------|---------|
| **macOS** | `brew install lilypond` |
| **Linux** | `sudo apt install lilypond` |
| **Windows** | Download from [lilypond.org](https://lilypond.org/download.html) |

---

## Troubleshooting

**`ImportError: libcsound64.so: cannot open shared object file`** (Linux)  
Csound is not on the library path. Try: `sudo apt install csound` and restart your terminal.

**`ctcsound` crashes on import** (macOS)  
The Csound framework is not found. Make sure Csound is installed and `/Library/Frameworks/CsoundLib64.framework` exists.

**`ctcsound` crashes on import** (Windows)  
`csound64.dll` is not on PATH. Re-run the Csound installer and ensure "Add to PATH" was selected, then restart your terminal.

**`No module named 'sounddevice'` or audio errors** (Linux)  
Install PortAudio: `sudo apt install portaudio19-dev`, then reinstall sounddevice: `pip install --force-reinstall sounddevice`.
