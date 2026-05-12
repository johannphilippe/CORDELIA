import json
import re
import soundfile as sf

import librosa
import numpy as np
from pathlib import Path

'''
This script make principally the .JSON for the instrument
'''

HARD_RESET = False
HARD_RESET_with_anal = False

# cordelia/script/make/instr.py -> make/ -> script/ -> cordelia/ -> project root
_PKG  = Path(__file__).resolve().parent.parent.parent
_ROOT = _PKG.parent

class Input_file:
    def __init__(self, path):
        self.path = path
        self.name = Path(path).stem
        self.extension = Path(path).suffix[1:]
        self.dir = Path(path).parent

audio_extensions = ['.flac', '.wav']

default_sonvs_dir = _PKG / 'default' / 'sonvs'
default_sonvs = {}
for _p in default_sonvs_dir.iterdir():
	if _p.suffix == '.orc':
		default_sonvs[_p.stem] = str(_p.relative_to(_ROOT))

def extract_global_vars(path, name):
	content = open(path, encoding='utf-8').read()
	gk_vars = list(set(re.findall(r'\bgk' + name + r'\w+', content)))
	gi_vars = list(set(re.findall(r'\bgi' + name + r'\w+', content)))
	return gk_vars + gi_vars

def process_instr(directory, json_file):
	for p in Path(directory).rglob('*'):
		if p.suffix == '.orc' and p.stem not in json_file:
			json_file[p.stem] = {
				'type': 'instr',
				'path': str(p.relative_to(_ROOT)),
				'global_var': extract_global_vars(p, p.stem)
			}
		elif p.suffix == '.py' and p.stem not in json_file:
			json_file[p.stem] = {
				'type': 'scripted_instr',
				'path': str(p.relative_to(_ROOT)),
				'extension': p.suffix
			}

def process_hybrid(directory, json_file):
	for p in Path(directory).rglob('*.orc'):
		if p.stem not in json_file:
			first_lines = open(p, encoding='utf-8').readlines()[:5]
			keyword = ';REQUIRE'
			required_instr = []

			for l in first_lines:
				if l.startswith(keyword):
					required_instr.extend(l.replace(keyword, '').strip().split(','))

			json_file[p.stem] = {
				'type': 'hybrid',
				'path': str(p.relative_to(_ROOT)),
				'required': required_instr,
				'global_var': extract_global_vars(p, p.stem)
			}

def sonvs_anal(directory):
	json_file = _PKG / 'config' / 'sonvs_anal.json'

	if HARD_RESET_with_anal or not json_file.exists():
		anals = {}
	else:
		with open(json_file, 'r', encoding='utf-8') as f:
			anals = json.load(f)

	for p in Path(directory).iterdir():
		rel = str(p.relative_to(_ROOT))
		if p.is_file() and p.suffix in audio_extensions and rel not in anals:
			audio, sr = librosa.load(p)
			f0 = librosa.yin(audio, fmin=25, fmax=3500)
			main_f0 = np.median(f0)
			anals[rel] = {'pitch': str(main_f0)}
	with open(json_file, 'w', encoding='utf-8') as f:
		json.dump(anals, f, indent=4)
	return anals
		
def get_audio_channels(file_path):
	with sf.SoundFile(file_path) as f:
		return f.channels

def process_sonvs(directory, json_file):

	anals_json = sonvs_anal(directory)

	for p in Path(directory).iterdir():
		if p.is_file():
			for variant in default_sonvs.keys():
				basename = p.stem
				if variant != '_':
					basename += variant

				if p.suffix in audio_extensions and basename not in json_file:
					print(f'{basename} is added.')
					rel = str(p.relative_to(_ROOT))
					json_file[basename] = {
						'type': 'sonvs',
						'channels': get_audio_channels(p),
						'path': [rel],
						'pitch': anals_json[rel]['pitch'],
						'orc': default_sonvs[variant]
					}
		else:
			audio_files = [str(f.relative_to(_ROOT)) for f in p.iterdir() if f.suffix in audio_extensions]

			if audio_files:
				for variant in default_sonvs.keys():
					basename = p.name
					if variant != '_':
						basename += variant
					json_file[basename] = {
						'type': 'dir_sonvs',
						'channels': get_audio_channels(str(_ROOT / audio_files[0])),
						'path': audio_files,
						'pitch': "440",
						'orc': default_sonvs[variant]
					}


def make(directory, json_file):
	json_file = Path(json_file)
	if HARD_RESET or not json_file.exists():
		instr_json = {}
	else:
		with open(json_file, 'r', encoding='utf-8') as f:
			instr_json = json.load(f)

	for subdir in Path(directory).iterdir():
		if subdir.name == 'instr':
			process_instr(subdir, instr_json)
		elif subdir.name == 'hybrid':
			process_hybrid(subdir, instr_json)
		elif subdir.name == 'sonvs':
			process_sonvs(subdir, instr_json)

	instr_json = dict(sorted(instr_json.items()))
	with open(json_file, 'w', encoding='utf-8') as f:
		json.dump(instr_json, f, indent=4)

