import json
import os.path as path
from pathlib import Path
from .path_func import get_reaper_project_info

BUFFER_SIZE = 512 * 512
MIDI_CORRECTION = 1024

# NAMES CONFIG
MAIN_TRACK_NAME = '_main'

MAIN_PROJECT_DIRECTORY, MAIN_PROJECT_NAME = get_reaper_project_info()
MAIN_RENDER_DIRECTORY_NAME = f'{MAIN_PROJECT_NAME}-cordelia_render'
MAIN_RENDER_DIRECTORY = path.join(MAIN_PROJECT_NAME, MAIN_RENDER_DIRECTORY_NAME)

# Sound files for feedback — set to None or point to your own files
SONVS_SUCCESS = None
SONVS_ERROR   = None

exluded_track_names = [MAIN_TRACK_NAME, 'cordelia']

# CORDELIA CONFIG
# rpr/^/cordelia_store/utils/config.py -> utils/ -> cordelia_store/ -> ^/ -> rpr/ -> project root
CORDELIA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

instr_json_path = CORDELIA_DIR / '_setting' / 'instr.json'
with open(instr_json_path, encoding='utf-8') as f:
	INSTR_JSON = json.load(f)

gen_json_path = CORDELIA_DIR / '_setting' / 'instr.json'
with open(gen_json_path, encoding='utf-8') as f:
	GEN_JSON = json.load(f)

def get_cordelia_include_paths():
	paths = [str(CORDELIA_DIR / '_core' / 'setting.orc')]
	with open(CORDELIA_DIR / '_core' / 'include.orc', encoding='utf-8') as f:
		for line in f:
			p = line.strip().replace('"', '').replace('#include ', '')
			paths.append(p)
	return paths

CORDELIA_INCLUDE_PATHs = get_cordelia_include_paths()