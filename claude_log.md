# CORDELIA — Cross-Platform Install Audit

**Date:** 2026-05-13  
**Scope:** Installation friction, platform blockers, and INSTALL.md accuracy  
**Platforms:** Linux (Ubuntu/Debian + other), macOS Silicon, macOS Intel, Windows 10/11

---

## 1. Critical blockers

### 1.1 `option.orc` has JACK enabled by default — breaks macOS and Windows

`cordelia/csound_cordelia/option.orc` currently has this line uncommented:

```
-+rtaudio=jack         ; Linux PipeWire-JACK / JACK
```

JACK/PipeWire-JACK is a Linux-only audio server. Csound will refuse to start on macOS and Windows because the JACK backend does not exist there. This is a **hard crash at startup** with a confusing error that does not point to any config file.

What the user must do (not documented in INSTALL.md):
- **macOS**: comment out `-+rtaudio=jack`, uncomment `;-+rtaudio=CoreAudio`
- **Windows**: comment out `-+rtaudio=jack`; Csound defaults to WinMME
- **Linux with PipeWire** (Ubuntu 22.04+): JACK line works, but `pipewire-jack` must be installed (`sudo apt install pipewire-jack`) — `install.sh` does not install it

Fix needed: document `option.orc` in INSTALL.md per platform, or patch it automatically in `install.sh`/`install.ps1`.

---

### 1.2 `dearpygui` has no macOS Intel wheels

`dearpygui` (in `requirements.txt`) publishes only `macosx_13_0_arm64` wheels — no `x86_64` Intel macOS wheel. On macOS Intel, `pip install -r requirements.txt` will either fail or attempt a source build requiring CMake, Metal SDK, and other non-trivial dependencies.

The GUI is commented out in `cordelia.py` (all `start_gui` calls are `#`-prefixed), so `dearpygui` is not used at runtime. But `pip install` still tries to install it.

Fix needed: move `dearpygui` out of the main `requirements.txt` into an optional `requirements-gui.txt`, or mark it as an extras dependency.

---

## 2. High-friction issues

### 2.1 `install.sh` Homebrew path is Apple Silicon–only

```bash
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
```

`/opt/homebrew` is the Apple Silicon Homebrew prefix. On macOS Intel, Homebrew lives at `/usr/local`. If brew is not already in PATH, this line silently does nothing on Intel Macs and subsequent `brew install csound` calls fail.

Fix needed:
```bash
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || \
eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null || true
```

### 2.2 `install.sh` is Debian/Ubuntu-only — other Linux distros hard-exit

```bash
if ! need apt-get; then
    echo "[!] This script supports Debian/Ubuntu (apt)."
    exit 1
fi
```

Arch, Fedora, openSUSE, NixOS users get a hard failure with no guidance. INSTALL.md covers the manual path but the script exit is abrupt.

Fix needed: instead of `exit 1`, print manual instructions and exit gracefully, or add minimal detection for `pacman`/`dnf`/`zypper`.

### 2.3 `pipewire-jack` not installed by `install.sh` on modern Linux

On Ubuntu 22.04+, PipeWire has replaced PulseAudio/JACK. The Csound JACK backend requires `pipewire-jack` to be present. `install.sh` installs `csound` and `portaudio19-dev` but not `pipewire-jack`. Without it, Csound starts but immediately fails to connect to JACK.

Fix needed: add `pipewire-jack` to the `install_linux` package list (or detect PipeWire vs native JACK first).

### 2.4 `numpy` upper bound missing in `requirements.txt` and `environment.yml`

| File | Constraint |
|------|-----------|
| `pyproject.toml` | `numpy = "^1.26.4"` → `>=1.26.4, <2.0.0` |
| `requirements.txt` | `numpy>=1.26.4` — no upper bound |
| `environment.yml` | `numpy>=1.26.4` — no upper bound |

`pip install -r requirements.txt` on a fresh system installs numpy 2.x, which has breaking API changes affecting `librosa` and potentially `ctcsound`. The current `.venv` has 1.26.4 (pinned at install time) but a new user will get 2.x.

Fix needed: `numpy>=1.26.4,<2.0.0` in both `requirements.txt` and `environment.yml`.

### 2.5 `winget install --id Csound.Csound` — package ID unverified

`install.ps1` uses this winget package ID. If Csound's winget manifest uses a different ID or is unavailable, the script fails with a cryptic winget error. The Csound `.exe` installer from csound.com is more reliable on Windows.

---

## 3. Medium friction / usability issues

### 3.1 `dac` and `adc` device files are developer-specific and undocumented

`cordelia/default/dac` and `cordelia/default/adc` list personal hardware names (Scarlett, Fireface, MacBook Pro, Bathys, okayo, JACQUES, …). A new user's audio device will not appear in these lists. `query_devices()` gracefully falls back to `['-odac']`, which usually works — but the user has no idea this happened and does not know these files exist or how to add their device.

Fix needed: add a section to INSTALL.md explaining these files, and add comments inside both files.

### 3.2 `--nchnls` is defined in two places with conflicting values

`option.orc` contains `--nchnls=4`, but `config.yaml` sets `channels.audio.count: 2`. `init_csound()` appends both; Csound uses the last value (2 from `config.yaml`), making the `--nchnls=4` in `option.orc` dead and misleading.

Fix needed: remove `--nchnls=N` from `option.orc` entirely — `cs.py` already handles it dynamically.

### 3.3 `gethostbyname(gethostname())` for UDP is fragile

In `utils/udp.py`:
```python
LOCALHOST = socket.gethostbyname(socket.gethostname())
```
Used as the OSC destination for the Reaper client. On some Linux setups (WSL, Docker, misconfigured `/etc/hosts`), this can raise `socket.gaierror` or return a non-loopback IP. The UDP servers always bind to `'localhost'` (127.0.0.1), so the asymmetry can cause packets to go astray.

Fix needed: `LOCALHOST = '127.0.0.1'`

### 3.4 `main_script.py` venv requirement is undocumented

Running `python cordelia/script/main_script.py` with the system Python fails (`ModuleNotFoundError: No module named 'soundfile'`, etc.). The venv Python must be used. This is not mentioned anywhere in INSTALL.md.

Fix needed: add a note in INSTALL.md, or add a wrapper script (`run_script.sh`).

### 3.5 Csound apt version may be below 6.17 on older Ubuntu

Ubuntu 20.04 ships Csound 6.14 via apt. `install.sh` runs `apt install csound` without checking the version afterward. `ctcsound>=6.17.1` will fail to import if the installed library is 6.14.

Fix needed: after `apt install csound`, check `csound --version` and warn if below 6.17.

---

## 4. Low friction / minor issues

### 4.1 `abjad` is a heavy dependency used in one function

`abjad` is used only in `ly_rhythm()` in `parser.py` (rhythm notation parsing). It is a large package with many sub-dependencies. No user-facing impact at install time (wheels exist for all platforms), but install time and disk use are non-trivial. Consider making it optional if `ly_rhythm` is rarely used.

### 4.2 `ctcsound` sdist is harmless — no compilation needed

`ctcsound` is published as an sdist (source distribution) with no binary wheel. It is a pure Python package using `ctypes` — no C compiler is needed. `pip install ctcsound` works on all platforms. Users seeing "Building wheel for ctcsound" may be confused; it is harmless.

---

## 5. INSTALL.md accuracy check

| Section | Status |
|---------|--------|
| Option 1 `install.sh` (macOS/Linux) | **Partially accurate** — Homebrew Intel path bug; missing `pipewire-jack`; no mention of `option.orc` audio backend config |
| Option 1 `install.ps1` (Windows) | **Accurate** for the script; winget Csound ID unverified |
| Option 2 pixi (Linux/macOS) | **Accurate** — correctly excludes Windows |
| Option 3 manual — Csound | **Accurate** |
| Option 3 manual — Python | **Accurate** |
| Option 3 manual — venv | **Accurate** |
| Option 3 manual — Run | **Accurate** |
| Option 4 conda — Windows caveat | **Accurate** (conda-forge has no Csound for win-64, confirmed) |
| LilyPond section | **Accurate** — correctly marked optional |
| Troubleshooting `libcsound64.so` | **Accurate** |
| Troubleshooting `ctcsound` macOS | **Accurate** |
| Troubleshooting `ctcsound` Windows | **Accurate** |
| Troubleshooting `sounddevice` | **Accurate** |
| **Missing** — `option.orc` audio backend | **Not documented — critical gap** |
| **Missing** — `pipewire-jack` on modern Linux | **Not documented** |
| **Missing** — `dearpygui` macOS Intel issue | **Not documented** |
| **Missing** — `dac`/`adc` device customisation | **Not documented** |
| **Missing** — `main_script.py` venv requirement | **Not documented** |

---

## Summary — priority order

| Priority | Issue |
|----------|-------|
| 🔴 Critical | `option.orc` JACK default breaks macOS and Windows startup |
| 🔴 Critical | `dearpygui` has no macOS Intel wheel — pip install fails |
| 🟠 High | `install.sh` Homebrew path is Apple Silicon–only |
| 🟠 High | `install.sh` is apt-only — non-Debian Linux hard-exits |
| 🟠 High | `pipewire-jack` not installed by `install.sh` on modern Linux |
| 🟠 High | `numpy` upper bound missing in `requirements.txt` / `environment.yml` |
| 🟡 Medium | `winget` Csound package ID unverified |
| 🟡 Medium | `dac`/`adc` device files undocumented and developer-specific |
| 🟡 Medium | `--nchnls` defined twice with conflicting values |
| 🟡 Medium | `gethostbyname(gethostname())` fragile on misconfigured systems |
| 🟡 Medium | `main_script.py` venv requirement undocumented |
| 🟡 Medium | Csound apt version not checked after install |
| 🟢 Low | `abjad` heavy dependency, only used in one function |
| 🟢 Low | `ctcsound` sdist (harmless, pure Python ctypes) |

---

# CORDELIA — Python Portability Audit

**Date:** 2026-05-11  
**Scope:** Python-side issues only (no Csound `.orc`/`.sco` files)  
**Goal:** Make CORDELIA installable and runnable on Windows, Linux, and macOS without modification.

---

## CRITICAL — Hardcoded Absolute Paths

### 1. `cordelia/constants/path.py` (line 3)
```python
cordelia_dir = '/Users/j/Documents/PROJECTs/CORDELIA/'
```
Hardcoded macOS user home path. Breaks on Windows and Linux entirely.

### 2. `cordelia/script/main_script.py` (line 5)
```python
cordelia_dir = '/Users/j/Documents/PROJECTs/CORDELIA/'
```
Duplicate of the above.

### 3. `cordelia/src/read_config.py` (line 4)
```python
CONFIG_FILE_PATH = '/Users/j/Documents/PROJECTs/CORDELIA/cordelia/config.yaml'
```
Hardcoded absolute path to the config file.

### 4. `rpr/^/cordelia_store/utils/config.py` (lines 22, 33–34)
```python
CORDELIA_DIR = '/Users/j/Documents/PROJECTs/CORDELIA'
paths = [CORDELIA_DIR + '/_core/setting.orc']
with open(CORDELIA_DIR + '/_core/include.orc') as f:
```
Hardcoded macOS path used with string concatenation instead of `pathlib`.

### 5. `rpr/^/*23/cordelia_store-v2.py` (lines 6, 9–10)
```python
CORDELIA_DIR = '/Users/j/Documents/PROJECTs/CORDELIA'
SONVS_SUCCESS = '/Users/j/Documents/script/OOT_Get_Heart.wav'
SONVS_ERROR   = '/Users/j/Documents/script/OOT_Navi_WatchOut1.wav'
```
Multiple hardcoded user-specific paths.

---

## CRITICAL — Hardcoded Executable Paths (Unix-only)

### 6. `cordelia/csoundAPI/cs.py` (line 51)
```python
output = subprocess.run(['/usr/local/bin/csound', ...], ...)
```
Hardcoded Unix Csound binary path. Does not exist on Windows.

### 7. `rpr/cordelia_csound/csound_methods/ATS.py` (lines 10, 79)
```python
homebrew_directory = '/opt/homebrew/bin'          # macOS-only
csound_commands.append(['/usr/local/bin/atsa', ...])
```
`/opt/homebrew` only exists on Apple Silicon Macs. `atsa` path is also hardcoded.

### 8. `rpr/cordelia_csound/csound_methods/CS.py` (lines 10, 32)
```python
homebrew_directory = '/opt/homebrew/bin'
'/usr/local/bin/csound'
```
Same as above.

### 9. `rpr/cordelia_offline/methods/` — all method files
`ATS.py`, `CS.py`, `CDP.py`, `LPC.py`, `PVS.py`, `PVSrt.py` all repeat:
```python
homebrew_directory = '/opt/homebrew/bin'
output_tempdir = '/Users/j/Documents/temp/'
logging.basicConfig(filename='/Users/j/cordelia-script.log', ...)
'/usr/local/bin/csound'
'/usr/local/bin/atsa'
```
Six files with the same set of hardcoded macOS paths.

---

## CRITICAL — macOS-only Shell Commands

### 10. `rpr/^/*23/cordelia_store-v2.py` (lines 194, 207)
```python
subprocess.call(['chmod', '+x', cmd_file])   # Unix-only
subprocess.call(['osascript', '-e', script]) # macOS-only
```
`chmod` does not exist on Windows. `osascript` (AppleScript) is macOS-exclusive.

### 11. `rpr/^/cordelia_store/utils/main_func.py` (line 31, 46)
```python
subprocess.call(['osascript', '-e', script])
```
AppleScript execution — macOS-only.

### 12. `rpr/^/*/cordelia_store.py` (lines 47, 52)
```python
subprocess.call(['osascript', '-e', script])
```
Same AppleScript issue.

### 13. `rpr/^/_lilypond-def/txt2ly.py` (line 58)
```python
os.system(f'cp {LILYPOND_SETTING_DEFAULT} {output}')
```
Unix `cp` command. Windows equivalent is `copy`/`xcopy`. Use `shutil.copy2()` instead.  
Additionally, line 5 hardcodes `/Users/j/Documents/PROJECTs/CORDELIA/rpr/_lilypond-def/pre.ly`.

### 14. `rpr/^/*/score gen-v4.py`
```python
os.system(folder_command)  # mkdir
os.system('cp "' + IDRA_path + '" ...')
```
Unix `mkdir` and `cp` via `os.system()`. Also references `.command` files (macOS Terminal launcher format).

---

## HIGH — Path Separator / `pathlib` Gaps

### 15. `cordelia/constants/var.py` (line 23)
```python
key = file_path.split('/')[-1].split('.')[0]
```
Hardcoded forward slash. On Windows paths use `\`. Use `pathlib.Path(file_path).stem` instead.

### 16. `cordelia/script/make/instr.py` (line 31)
```python
key = file_path.split('/')[-1].split('.')[0]
```
Same issue.

### 17. `cordelia/constants/path.py` (line 5)
```python
cordelia_score = f'../_score/cor{cordelia_date}'
```
Relative path using `..` without anchoring to `__file__`. Breaks if the working directory is not the expected one.

---

## HIGH — Relative Paths Without Working-Directory Anchor

All of the following assume the process is launched from a specific directory. They will silently fail or load wrong files if the user runs the tool from anywhere else.

### 18. `cordelia/cordelia.py` (lines 42, 111, 130)
```python
with open('./csound_cordelia/setting.orc') as f:
with open('./csound_cordelia/include.orc', 'r') as f:
with open(f'./default/{converter}') as f:
```

### 19. `cordelia/constants/var.py` (lines 27–28, 32–33)
```python
json_dir   = './config/'
alias_path = './config/alias/alias.json'
```

### 20. `cordelia/csoundAPI/cs.py` (lines 42, 83, 110, 126, 129)
```python
with open('./csound_cordelia/option.orc') as f:
with open(f'./default/{converter}') as f:
```

### 21. `cordelia/script/main_script.py` (lines 7, 11, 14, 17, 20, 23)
```python
include_dir = './csound_cordelia/'
gen_json    = './config/GEN.json'
```

### 22. `cordelia/script/make/instr.py` (lines 26–27)
```python
default_sonvs_dir = './default/sonvs'
json_file = './config/sonvs_anal.json'
```

**Fix pattern for all of the above:**
```python
from pathlib import Path
BASE = Path(__file__).parent  # anchors to the file's own directory
config_path = BASE / 'config' / 'GEN.json'
```

---

## MEDIUM — Subprocess with `shell=True`

### 23. `rpr/^/exec_parallel.py` (lines 21, 32)
```python
subprocess.run(command, shell=True, ...)
```
`shell=True` invokes `/bin/sh` on Unix and `cmd.exe` on Windows. Command syntax differs between them. This is fragile and also a security risk if any part of `command` comes from user input.

---

## MEDIUM — Missing or Inconsistent Encoding Declarations

### 24. `cordelia/script/make/scala.py` (line 60)
```python
with open(file_path, 'r', encoding='latin1') as f:
```
Uses `latin1` while all other file opens in the project omit `encoding=` entirely. The default encoding is locale-dependent and differs between Windows (usually `cp1252`) and Linux/macOS (usually `UTF-8`).

### 25. All `open(...)` calls without `encoding=` throughout:
- `cordelia/constants/var.py`
- `cordelia/script/make/routing.py`, `gen.py`, `include.py`, `parser.py`, `tokens.py`
- `cordelia/src/read_config.py`
- `rpr/cordelia_offline/methods/*.py`

**Fix:** Always pass `encoding='utf-8'` (or the correct encoding) explicitly.

---

## MEDIUM — Audio Device Discovery Tied to Unix Csound Binary

### 26. `cordelia/csoundAPI/cs.py` (lines 40–51)
```python
def which_rtaudio():
    with open('./csound_cordelia/option.orc') as f:
        for line in f:
            if line.startswith('-+rtaudio='):
                return line

if which_rtaudio() != '-+rtaudio=jack':
    output = subprocess.run(['/usr/local/bin/csound', '--devices'], ...)
```
- Reads audio backend from a relative file path (fragile).
- Only checks for JACK; no consideration of CoreAudio (macOS), WASAPI/ASIO (Windows), or ALSA (Linux).
- Calls Csound via hardcoded Unix path.

---

## LOW — macOS-Specific Filesystem Artifacts

### 27. `cordelia/script/make/scala.py` (line 11)
```python
if filename != '.DS_Store' and extension == '.scl':
```
`.DS_Store` is a macOS metadata file. This works fine on other platforms (the file just never appears), but it signals macOS-centric development and may be a sign that similar assumptions exist elsewhere.

---

## Summary Table

| Severity | Count | Category |
|----------|-------|----------|
| Critical | 14 issues (30+ lines) | Hardcoded absolute paths, Unix executables, macOS-only commands |
| High     | 11 issues             | Path separators, relative paths without anchor |
| Medium   | 4 issues              | Encoding, subprocess shell, audio device discovery |
| Low      | 1 issue               | macOS filesystem artifact filter |

---

## Recommended Fix Strategy

1. **Single source-of-truth for the project root.** Add a `cordelia/constants/path.py` that derives the root from `Path(__file__).parent.parent` and export it everywhere. Delete all hardcoded absolute paths.

2. **Replace all `os.path` string manipulation with `pathlib.Path`.** Eliminates separator issues automatically.

3. **Locate executables with `shutil.which()`.** Replace every `/usr/local/bin/csound` with `shutil.which('csound')` and raise a clear error if not found.

4. **Replace all `os.system('cp ...')` and `os.system('mkdir ...')` with `shutil` equivalents.** `shutil.copy2()`, `Path.mkdir(parents=True, exist_ok=True)`.

5. **Remove all `osascript`/AppleScript calls.** Either drop the feature or gate it behind `if sys.platform == 'darwin':` with a cross-platform fallback.

6. **Always specify `encoding='utf-8'`** on every `open()` call.

7. **For audio backend detection,** read Csound's `--devices` output using the detected `csound` binary (from `shutil.which`), not a hardcoded path.

8. **Use `tempfile.gettempdir()`** for all temporary files instead of `/Users/j/Documents/temp/`.

9. **Use `logging.basicConfig(filename=BASE / 'cordelia.log')`** so log files land next to the project, not in a hardcoded user directory.

---

## Fix Log

### Step 1 — Single source of truth for the project root (2026-05-11)

Replaced all hardcoded `/Users/j/Documents/PROJECTs/CORDELIA` absolute paths with `pathlib.Path`-based derivations anchored to each file's own `__file__`. Five files changed:

**`cordelia/constants/path.py`**
- Added `from pathlib import Path`
- Introduced `CORDELIA_ROOT = Path(__file__).resolve().parent.parent.parent` (project root) and `CORDELIA_PKG = Path(__file__).resolve().parent.parent` (the `cordelia/` package dir)
- `cordelia_dir` kept as a legacy alias pointing to `CORDELIA_ROOT`
- `cordelia_score` converted from an `f'../_score/...'` string to `CORDELIA_ROOT / '_score' / f'cor{cordelia_date}'`

**`cordelia/script/main_script.py`**
- Removed local `cordelia_dir = '/Users/j/...'` declaration
- Removed `import os` (no longer needed)
- All paths (`include_dir`, `gen_dir`, `gen_json`, `instr_dir`, `instr_json`, `routing_dir`, `routing_json`, `routing_orc`, `scala_dir`, `scala_json`, `tokens_json`) rebuilt using `CORDELIA_ROOT` and `CORDELIA_PKG` with `/` operators instead of `os.path.join`
- `_cordelia/csound_cordelia` legacy path corrected to `CORDELIA_PKG / 'csound_cordelia'`

**`cordelia/src/read_config.py`**
- Added `from pathlib import Path`
- `CONFIG_FILE_PATH` replaced with `Path(__file__).resolve().parent.parent / 'config.yaml'`
- Added `encoding='utf-8'` to the `open()` call (early fix ahead of Step 6)

**`rpr/^/cordelia_store/utils/config.py`**
- Added `from pathlib import Path`
- `CORDELIA_DIR` replaced with `Path(__file__).resolve().parent.parent.parent.parent.parent` (5 levels up to project root); comment documents the directory chain
- All string concatenations (`CORDELIA_DIR + '/_core/...'`) replaced with `/`-operator path joins
- `SONVS_SUCCESS` / `SONVS_ERROR` set to `None` (were pointing to personal sound files outside the repo; need to be made user-configurable in a later step)
- Added `encoding='utf-8'` to all `open()` calls in this file

**`rpr/^/*23/cordelia_store-v2.py`**
- Added `from pathlib import Path`
- `CORDELIA_DIR` replaced with `Path(__file__).resolve().parent.parent.parent.parent` (4 levels up to project root); comment documents the directory chain
- `SONVS_SUCCESS` / `SONVS_ERROR` set to `None`
- String concatenations for `_setting/instr.json` and `_setting/gen.json` replaced with `/`-operator joins
- Added `encoding='utf-8'` to those `open()` calls

---

### Step 2 — Replace `os.path` string manipulation with `pathlib.Path` (2026-05-11)

Eliminated all `split('/')` path hacks and unanchored `'./relative'` strings. Eight files changed:

**`cordelia/constants/var.py`**
- Removed `import os`; added `from pathlib import Path`
- Added `_PKG = Path(__file__).resolve().parent.parent` to anchor to the `cordelia/` package dir (cannot import from `constants.path` — circular dependency)
- `json_dir = './config/'` → `_PKG / 'config'`
- `alias_path` and `complex_path` string literals → `_PKG / 'config' / 'alias' / ...`
- `os.listdir` + `os.path.join` loop → `Path(directory).iterdir()`
- `file_path.split('/')[-1].split('.')[0]` → `file_path.stem`
- Added `encoding='utf-8'` to all `open()` calls in this file

**`cordelia/script/make/instr.py`**
- Added `_PKG = Path(__file__).resolve().parent.parent.parent` (3 levels up to `cordelia/`)
- Removed `import os` (was the last consumer)
- `default_sonvs_dir = './default/sonvs'` → `_PKG / 'default' / 'sonvs'`
- `os.listdir` + `os.path.join` loop for sonvs → `Path.iterdir()`
- `file_path.split('/')[-1].split('.')[0]` → `p.stem`
- `process_instr` / `process_hybrid`: `os.walk` + `os.path.join` + `os.path.splitext` → `Path.rglob('*.orc')`, `p.stem`, `p.suffix`, `str(p)` for JSON values
- `sonvs_anal`: `'./config/sonvs_anal.json'` → `_PKG / 'config' / 'sonvs_anal.json'`; `os.path.exists` → `.exists()`; `os.path.isfile` → `.is_file()`; `os.path.join` → `/` operator; paths stored in JSON converted with `str()`
- `make`: `os.path.exists` → `Path(json_file).exists()`; `os.listdir` → `Path.iterdir()`; `os.path.join` removed

**`cordelia/script/make/gen.py`**
- Removed `import os`; added `from pathlib import Path`
- `os.walk` + `os.path.splitext` + `os.path.join` → `Path(directory).rglob('*.orc')` with `p.stem`
- Added `encoding='utf-8'` to both `open()` calls

**`cordelia/script/make/routing.py`**
- Removed `import os`; added `from pathlib import Path`
- `os.listdir` + `f.split('.')[0]` + `os.path.join` → `Path(directory).iterdir()` with `p.stem` and `p.suffix`
- Added `encoding='utf-8'`

**`cordelia/script/make/scala.py`**
- Removed `import os`; added `from pathlib import Path`
- `find_duplicate_files`: `os.walk` + `os.path.splitext` + `filename != '.DS_Store'` filter → `Path.rglob('*.scl')` (glob already excludes non-`.scl` files)
- `find_nonstandard_names`: same migration; `.DS_Store` check dropped (irrelevant on non-macOS)
- `process_scala`: `os.walk` loop → `Path.rglob('*.scl')`; `os.path.join` + `os.path.splitext` removed; `'path': file_path` → `'path': str(p)` for JSON safety
- Added `encoding='utf-8'` to JSON write

**`cordelia/script/make/include.py`**
- Removed `import os`; added `from pathlib import Path`
- `os.walk` + `f.split('.')[0]` + `os.path.join` → `Path(directory).rglob('*.orc')` with `p.stem`
- Excluded stems (`option`, `include`, `setting`) checked via set membership
- Added `encoding='utf-8'`

**`cordelia/cordelia.py`**
- Removed `os` from `import os, sys` (only `sys` still needed)
- Added `_PKG = Path(__file__).resolve().parent`
- `os.path.join(input_dir, ...)` → `input_dir / (input_name + '-cordelia.orc')` (`input_dir` is already a `Path`)
- `'./csound_cordelia/setting.orc'` and `'./csound_cordelia/include.orc'` → `_PKG / 'csound_cordelia' / ...`
- Added `encoding='utf-8'` to file opens

**`cordelia/csoundAPI/cs.py`**
- Removed `os` from `import re, os`; added `from pathlib import Path`
- Added `_PKG = Path(__file__).resolve().parent.parent`
- `create_dir`: `os.path.exists` + `os.mkdir` → `Path(directory).mkdir(parents=True, exist_ok=True)`
- `which_rtaudio`: `'./csound_cordelia/option.orc'` → `_PKG / 'csound_cordelia' / 'option.orc'`
- `query_devices`: `f'./default/{converter}'` → `_PKG / 'default' / converter`
- `init_csound`: all three `'./csound_cordelia/...'` literals → `_PKG / 'csound_cordelia' / ...`
- Added `encoding='utf-8'` to all `open()` calls in this file

---

### Step 3 — Locate executables with `shutil.which()` (2026-05-11)

Removed all hardcoded executable paths (`/usr/local/bin/csound`, `/usr/local/bin/atsa`, `/opt/homebrew/bin`) and the `os.environ['PATH']` manipulation that accompanied them. `shutil` is stdlib — no new dependency. Eleven Python files changed.

**`cordelia/csoundAPI/cs.py`**
- Added `import shutil`
- `get_devices()`: replaced `/usr/local/bin/csound` with `shutil.which('csound')` and a `RuntimeError` if not found

**`rpr/cordelia_offline/methods/_func.py`** and **`rpr/cordelia_csound/csound_methods/_func.py`** (identical change to both)
- Added `import shutil`, `import sys`, `from pathlib import Path`
- Added `find_executable(name)`: tries `shutil.which` first; falls back to platform-specific common directories (`/opt/homebrew/bin`, `/usr/local/bin` on macOS; `/usr/local/bin`, `/usr/bin` on Linux; no fallback on Windows); raises `RuntimeError` with an install hint if not found

**`rpr/cordelia_offline/methods/ATS.py`** and **`rpr/cordelia_csound/csound_methods/ATS.py`**
- Removed `homebrew_directory = '/opt/homebrew/bin'` and `os.environ['PATH']` prepend
- `/usr/local/bin/atsa` → `find_executable('atsa')` (imported from `_func`)

**`rpr/cordelia_offline/methods/CS.py`** and **`rpr/cordelia_csound/csound_methods/CS.py`**
- Removed `homebrew_directory` and `os.environ['PATH']` prepend; added `import shutil`
- `/usr/local/bin/csound` → `shutil.which('csound')` with `RuntimeError` if `None`

**`rpr/cordelia_offline/methods/CDP.py`** and **`rpr/cordelia_csound/csound_methods/CDP.py`**
- Removed `/Applications/cdpr8/_cdp/_cdprogs` PATH prepend (no subprocess calls to CDP binaries in these files)

**`rpr/cordelia_offline/methods/LPC.py`, `PVS.py`, `PVSrt.py`** and **`rpr/cordelia_csound/csound_methods/LPC.py`, `PVS.py`, `PVSrt.py`** (6 files)
- Removed `homebrew_directory` and `os.environ['PATH']` prepend from all six (use ctcsound API, not subprocess)

**`rpr/cordelia_releted/cordelia-commit_tuning.py`**
- Removed `homebrew_directory` and `os.environ['PATH']` prepend
- Fixed `CORDELIA_DIR` to `Path(__file__).resolve().parent.parent.parent`; paths converted to `/` operator

**`rpr/test/abjad-test.py`**
- Removed `import os`, `homebrew_directory`, and `os.environ['PATH']` prepend

---

### Step 4 — Replace `os.system('cp'/'mkdir'/'rm -r')` with `shutil`/`pathlib` (2026-05-11)

Replaced all shell-out file operations with cross-platform Python equivalents. 15 Python files changed. No new dependencies (`shutil` and `pathlib` are stdlib).

Mappings applied:
- `os.system('mkdir X')` → `Path(X).mkdir(parents=True, exist_ok=True)`
- `os.system('cp src dst')` → `shutil.copy2(src, dst)`
- `os.system('rm -r X')` + `if os.path.isdir` guard → `shutil.rmtree(X, ignore_errors=True)` (guard removed)
- `var = 'cp A B'; os.system(var)` → `shutil.copy2(A, B)` (intermediate variable removed)

**`rpr/^/_lilypond-def/txt2ly.py`**
- Added `import shutil`; removed `import os`
- Fixed leftover hardcoded `LILYPOND_SETTING_DEFAULT` → `Path(__file__).resolve().parent / 'pre.ly'`
- `os.path.join` + `os.system('cp ...')` → `Path(file).parent / ...` + `shutil.copy2`

**14 score-gen Reaper scripts** (all in `rpr/^/*/` and `rpr/^/*/*/`):
Added `import shutil` and `from pathlib import Path` to all 14, then applied per-file replacements.

Group A (simple mkdir + cp): `score gen-v4.py`, `score gen v3_quick.py`, `score gen v3.py`, `score gen quick v4.py`, `score gen v2.py`, `score gen v2_noopen.py`, `score_gen.py`, `CORDELIA score gen-v5.py`, `CORDELIA score gen quick v5.py`

Group B (rm-r + mkdir + mkdir-in-loop + cp): `score gen each v4.py`, `score gen each v5.py`, `score gen track v3.py`, `score gen track.py`, `CORDELIA score gen each v6.py`

**Deferred to Step 5**: Four files (`score gen v3_quick.py`, `score gen quick v4.py`, `score gen v2.py`, `CORDELIA score gen quick v5.py`) still contain `os.system('open ...')` calls that open macOS `.command` Terminal launcher files — macOS-only behaviour handled in Step 5.

---

### Step 5 — Replace osascript / AppleScript with cross-platform subprocess + sounddevice (2026-05-11)

Strategy: drop the macOS Terminal window entirely (osascript removed), run Csound via `subprocess.Popen` piping stdout/stderr, play audio feedback with `sounddevice`+`soundfile` instead of `afplay`.

New Python dependencies added to `pyproject.toml`:
- `sounddevice = "^0.4.6"` (audio playback)
- `soundfile = "^0.12.1"` (audio file decoding)

`play_sound(path)` helper added (silently no-ops if path is `None` or if libraries are missing):
```python
def play_sound(path):
    if not path:
        return
    try:
        import sounddevice as sd
        import soundfile as sf
        data, sr = sf.read(path)
        sd.play(data, sr)
        sd.wait()
    except Exception:
        pass
```

**`rpr/^/*/cordelia_store.py`**
- Removed `osascript` call and its `script` variable (lines 264–266)
- Kept the existing `subprocess.Popen(command, shell=True); p.wait()` block that was already there

**`rpr/^/cordelia_store/utils/main_func.py`**
- Removed multi-line AppleScript `script` variable and `subprocess.call(['osascript', ...])` call
- Uncommented and cleaned up the `subprocess.Popen` + `p.communicate()` block
- Added `play_sound(SONVS_SUCCESS)` on success, `play_sound(SONVS_ERROR)` + `break` on failure
- Added `from .config import SONVS_SUCCESS, SONVS_ERROR`
- Added `play_sound()` helper before `execute_csound()`

**`rpr/^/*23/cordelia_store-v2.py`**
- Removed `cmd_file` creation, `subprocess.call(['chmod', '+x', cmd_file])`, AppleScript `script` variable, and `osascript` call
- Uncommented and cleaned up `subprocess.Popen` + `p.communicate()` block
- Added `play_sound(SONVS_SUCCESS/SONVS_ERROR)` calls
- Added `play_sound()` helper before `execute_csound()`

**4 score-gen scripts** (`score gen v3_quick.py`, `score gen v2.py`, `score gen quick v4.py`, `CORDELIA score gen quick v5.py`)
- Removed `os.system('open ...')` lines (macOS-only `.command` file launcher)

---

### Step 6 — Add `encoding='utf-8'` to all `open()` calls (2026-05-11)

All text-mode `open()` calls now explicitly use `encoding='utf-8'`. This prevents silent corruption of file names, Csound syntax, microtonal symbols, and instrument definitions when the system locale is not UTF-8 (common on Windows, some Linux setups).

Two passes run via Python script across the entire codebase:

**Pass 1** — explicit text modes (`'r'`, `'w'`, `'a'`, `'r+'`, etc.):
- Pattern: `open(X, 'mode')` → `open(X, 'mode', encoding='utf-8')`
- Binary modes (`'rb'`, `'wb'`, `'ab'`) left untouched
- 57 files updated

**Pass 2** — no-mode calls (default `'r'` text):
- Pattern: `open(X)` → `open(X, encoding='utf-8')`
- Skipped if content already contained a quoted mode char or `encoding=`
- 14 files updated (includes `parser.py`, `cordelia_store.py`, `cordelia_store-v2.py`, `Insert tuning.py`, OSC send scripts, `cordelia-commit_tuning.py`)

Side-effect: `subprocess.Popen` also matched the `open(` regex — result is `encoding='utf-8'` added to two ATS.py Popen calls. This is valid Python 3.x (changes stdout/stderr type from bytes to str); output is not consumed as bytes in these sites so behaviour is unchanged.

Files **not** changed: binary-mode opens (`'rb'`/`'wb'`), files with `encoding=` already present from Steps 1–5.

---

### Step 7 — Fix audio backend detection in `cordelia/csoundAPI/cs.py` (2026-05-11)

Two bugs in `which_rtaudio()` / `get_devices()` that would crash on any platform if `option.orc` lacked a `-+rtaudio=` line, and silently fail when JACK was spelled with different casing.

**`cordelia/csoundAPI/cs.py`**

`which_rtaudio()`:
- Added explicit `return None` at the end (was implicit; makes the contract clear and enables safe callers)

`get_devices()`:
- Cached `which_rtaudio()` into a local `rtaudio` variable (was called twice; second call during `subprocess.run([csound, which_rtaudio(), ...])` would crash with `TypeError: expected str not None` if no rtaudio option is set)
- Added `rtaudio is None` guard → returns `[]`, falling through to `query_devices()`'s `['-odac', '-iadc']` default
- Made JACK check case-insensitive: `rtaudio.lower() == '-+rtaudio=jack'` (was exact-string match, missed `JACK` / `Jack`)
- Simplified `[device for device in devices]` to `list(devices)` (no-op list copy)

No new dependencies. No behaviour change on correctly-configured systems.

---

### Step 8 — Replace hardcoded temp directories with `tempfile.gettempdir()` (2026-05-11)

13 files had a hardcoded personal macOS path used as a working directory for intermediate analysis files (mono WAV splits, ATS analysis files, LPC/PVS intermediates, Csound score/orc temp files):

```python
# Before
output_tempdir = '/Users/j/Documents/temp/'
```

```python
# After
import tempfile
output_tempdir = tempfile.gettempdir()
```

`tempfile.gettempdir()` returns the correct platform temp directory:
- `/tmp` on Linux / macOS
- `C:\Users\<user>\AppData\Local\Temp` on Windows

`import tempfile` was inserted automatically after the last top-level import in each file.

**Files changed (13):**
- `rpr/cordelia_offline/methods/` — ATS.py, CDP.py, CS.py, LPC.py, PVS.py, PVSrt.py
- `rpr/cordelia_csound/csound_methods/` — ATS.py, CDP.py, CS.py, LPC.py, PVS.py, PVSrt.py
- `rpr/^/wtes copy.py` (had `/Users/j/Documents/PROJECTs/_temp`)

All downstream uses of `output_tempdir` (`os.path.join`, `os.listdir`) work unchanged since `tempfile.gettempdir()` returns a plain string.

Note: the `logging.basicConfig(filename='/Users/j/cordelia-script.log', ...)` in the same files is left for Step 9.

---

### Step 9 — Fix hardcoded log file paths (2026-05-11)

All 12 method scripts in `cordelia_offline/methods/` and `cordelia_csound/csound_methods/` had a personal macOS path hardcoded as the logging target:

```python
# Before
logging.basicConfig(filename='/Users/j/cordelia-script.log', level=logging.DEBUG, filemode='w')
```

```python
# After
logging.basicConfig(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cordelia-script.log'), level=logging.DEBUG, filemode='w')
```

The log file is now written next to the script itself (e.g. `rpr/cordelia_offline/methods/cordelia-script.log`). `os.path` was already imported in all 12 files, so no new dependency needed. `filemode='w'` (overwrite on each run) is preserved — behaviour is unchanged.

**Files changed (12):**
- `rpr/cordelia_offline/methods/` — ATS.py, CDP.py, CS.py, LPC.py, PVS.py, PVSrt.py
- `rpr/cordelia_csound/csound_methods/` — ATS.py, CDP.py, CS.py, LPC.py, PVS.py, PVSrt.py

---

## INSTALLATION — Beginner-Friendly Strategy (2026-05-11)

### The core challenge

CORDELIA has two distinct installation layers that cannot both be handled by `pip` alone:

| Layer | What | How it is found at runtime |
|---|---|---|
| **System** | Csound shared library | `libcsound64.so` (Linux), `CsoundLib64` framework (macOS), `csound64.dll` on PATH (Windows) |
| **System** | PortAudio (for `sounddevice`) | system lib; bundled in wheel on Windows, separate install on Linux/macOS |
| **Python** | All deps in `pyproject.toml` | pip / poetry |

`ctcsound` is pure Python (`ctypes`). It does **not** link at compile time — it calls `CDLL` at import time:

```python
# Linux
libcsound = ct.CDLL("libcsound64.so")
# Windows
libcsound = ct.CDLL(ctypes.util.find_library("csound64"))
# macOS
libcsound = ct.CDLL(ctypes.util.find_library("CsoundLib64"))
```

This means: Csound **must** be installed and its library visible on the system path before Python starts. A pure pip install will never be enough.

`abjad` imports fine without LilyPond — it's only needed if you actually render `.ly` scores (notation output). For core live-coding use, LilyPond is optional.

---

### Dependency nature summary

| Package | Type | Extra system dep? |
|---|---|---|
| `numpy`, `rapidfuzz`, `pyyaml` | binary wheels, all platforms | none |
| `librosa`, `python-osc`, `abjad`, `rich` | pure Python | none |
| `dearpygui` | binary wheels, all platforms | none |
| `soundfile` | binary wheel with bundled libsndfile | none |
| `sounddevice` | binary wheel | **PortAudio** (Linux/macOS; bundled on Windows) |
| `ctcsound` | pure Python ctypes | **Csound shared library** (all platforms) |

---

### Options compared

#### Option A — pixi (best for a single-tool unified install)

[pixi](https://pixi.sh) is a modern cross-platform package manager (2023, by prefix.dev) that installs packages from conda-forge — including both Python and compiled system libraries — without requiring any pre-existing Python or conda installation.

```
# one-line pixi install (macOS/Linux)
curl -fsSL https://pixi.sh/install.sh | bash
# Windows: winget install prefix-dev.pixi
```

Then:
```
cd CORDELIA
pixi install
pixi run cordelia   # if a task is defined in pixi.toml
```

Csound is available on conda-forge for **Linux-64, macOS (x86\_64 + arm64)**. Windows conda-forge Csound packaging is partial — the official Windows Csound installer remains more reliable there.

A `pixi.toml` would declare:

```toml
[project]
name = "cordelia"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "osx-arm64"]

[dependencies]
python = ">=3.11"
csound = ">=6.17"
portaudio = "*"

[pypi-dependencies]
librosa = ">=0.10.1"
numpy = ">=1.26.4"
ctcsound = ">=6.17.1"
python-osc = ">=1.8.3"
abjad = ">=3.19"
pyyaml = ">=6.0.2"
rich = ">=13.9.4"
dearpygui = ">=2.0.0"
rapidfuzz = ">=3.14.3"
sounddevice = ">=0.4.6"
soundfile = ">=0.12.1"

[tasks]
cordelia = "python cordelia/cordelia.py"
```

**Pro**: zero prior setup; one tool handles Python version, Csound, PortAudio, and all pip deps  
**Con**: Windows Csound on conda-forge is not reliable yet; pixi is unfamiliar to non-technical users

---

#### Option B — conda/Miniforge environment.yml (alternative to pixi)

Miniforge is a minimal Conda installer that defaults to conda-forge. More established than pixi, slower but proven.

```bash
# After installing Miniforge:
conda env create -f environment.yml
conda activate cordelia
python cordelia/cordelia.py
```

`environment.yml`:
```yaml
name: cordelia
channels:
  - conda-forge
dependencies:
  - python=3.11
  - csound>=6.17
  - portaudio
  - pip
  - pip:
    - librosa>=0.10.1
    - numpy>=1.26.4
    - ctcsound>=6.17.1
    - python-osc>=1.8.3
    - abjad>=3.19
    - pyyaml>=6.0.2
    - rich>=13.9.4
    - dearpygui>=2.0.0
    - rapidfuzz>=3.14.3
    - sounddevice>=0.4.6
    - soundfile>=0.12.1
```

Same Windows caveat as pixi.

---

#### Option C — Official installers + pip (most reliable cross-platform, recommended for Windows)

Steps:
1. Download and install **Csound** from [csound.github.io/csound/downloads](https://csound.github.io/csound/downloads) (`.exe` / `.pkg` / `.deb`)
   - The installer adds Csound to PATH / system lib paths automatically
2. Download and install **Python 3.11+** from [python.org](https://python.org)
   - On Windows: tick "Add Python to PATH"
3. In a terminal: `pip install -r requirements.txt` (or `poetry install`)

For PortAudio on Linux/macOS: `sudo apt install portaudio19-dev` / `brew install portaudio`

**Pro**: most reliable on all three platforms; uses familiar GUI installers; no new tools to learn  
**Con**: three separate installation steps; requires knowing what a terminal is

---

#### Option D — Shell install scripts (wraps Option C for true beginners)

A pair of scripts that automates Option C end-to-end:

`install.sh` (macOS/Linux):
```bash
#!/usr/bin/env bash
set -e
# macOS: install Csound via Homebrew; Linux: apt
if [[ "$OSTYPE" == "darwin"* ]]; then
    command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    brew install csound portaudio
else
    sudo apt-get update && sudo apt-get install -y csound portaudio19-dev
fi
pip3 install -r requirements.txt
echo "CORDELIA installed. Run: python3 cordelia/cordelia.py"
```

`install.ps1` (Windows PowerShell):
```powershell
# Requires winget (Windows 10/11)
winget install Csound.Csound
winget install Python.Python.3.11
pip install -r requirements.txt
Write-Host "CORDELIA installed. Run: python cordelia\cordelia.py"
```

**Pro**: single command for beginners; hides complexity; cross-platform  
**Con**: requires `winget` (Win10/11 only), Homebrew on macOS, or sudo on Linux; the script itself must be maintained

---

### Recommendation

| Target user | Recommended path |
|---|---|
| macOS/Linux beginner | **pixi** — single binary, one `pixi install`, zero prior Python needed |
| Windows beginner | **Option C** — official Csound .exe + Python .exe + `pip install -r requirements.txt` |
| All platforms, repeatable | **conda/Miniforge** with `environment.yml` (Windows: still needs official Csound installer) |
| Fully automated CI/script | **install.sh + install.ps1** wrapping Option C |

### Concrete next actions (if pursued)

1. Add `pixi.toml` to repo (enables `pixi install` on Linux/macOS)
2. Add `environment.yml` for conda users
3. Generate `requirements.txt` from poetry: `poetry export -f requirements.txt --without-hashes > requirements.txt`
4. Add `install.sh` + `install.ps1` scripts
5. Write a `INSTALL.md` with four tab sections: Windows / macOS / Linux / pixi
6. Consider extracting a "minimal" `requirements-minimal.txt` that drops `abjad` + LilyPond for users who don't need notation output

### Scope clarification (live-coding only, no Reaper)

The target installation is **only the `cordelia/` live-coding engine** — the Python package that parses instructions and sends them to Csound. The entire `rpr/` directory (Reaper score-gen scripts, offline render tools, DAW integration) is out of scope.

This does **not** reduce the Python dependency list:
- `abjad` is needed inside `cordelia/src/parser.py` — it drives `ReducedLyParser` for rhythm notation parsing, which is core to the live-coding instruction language
- `librosa` is needed inside `cordelia/script/make/instr.py` — used for pitch detection (YIN algorithm) when analysing sample instruments
- `abjad` does **not** require LilyPond to be installed — the Python API works without it; LilyPond is only needed to render notation to PDF/PNG, which is an optional workflow

What changes with no-Reaper scope:
- **No Reaper DAW** needs to be installed
- **No Reaper scripts** need to be copied or configured
- The `rpr/` directory can be ignored entirely
- `sounddevice`/`soundfile` (added in Step 5 for audio feedback in Reaper render loops) remain in deps but are lightweight

Revised minimal install (live-coding only):

| What | How |
|---|---|
| Python 3.11 | python.org / pixi / conda |
| Csound 6.17 | csound.github.io / brew / apt / pixi |
| PortAudio | bundled on Windows; `brew install portaudio` / `apt install portaudio19-dev` |
| Python deps | `pip install -r requirements.txt` |

The `pixi` single-command path (Linux/macOS) is still the most beginner-friendly.

### Files created (concrete next actions completed, 2026-05-11)

| File | Purpose |
|------|---------|
| `requirements.txt` | Flat pip requirements derived from `pyproject.toml`; used by install scripts and Option 3 manual install |
| `pixi.toml` | pixi project config; declares Python 3.11+, Csound, PortAudio from conda-forge, all pip deps; defines `pixi run cordelia` task; supports linux-64, osx-64, osx-arm64 |
| `environment.yml` | conda/Miniforge environment; conda-forge channel; Csound + PortAudio as conda deps, Python deps via pip section |
| `install.sh` | Bash installer for macOS (Homebrew) and Linux (apt); installs Csound, PortAudio, Python 3.11, then `pip install -r requirements.txt`; executable (`chmod +x`) |
| `install.ps1` | PowerShell installer for Windows; uses `winget` to install Csound and Python 3.11, then `pip install -r requirements.txt` |
| `INSTALL.md` | User-facing installation guide with four options (script / pixi / manual / conda) plus LilyPond optional note and troubleshooting section |
