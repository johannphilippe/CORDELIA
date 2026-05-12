import json
from pathlib import Path
from datetime import datetime

# cordelia/constants/var.py -> constants/ -> cordelia/
_PKG = Path(__file__).resolve().parent.parent

cordelia_init_code = []
cordelia_compile = []

cordelia_given_else = []
cordelia_given_instr = ['mouth']

cordelia_instr_start_num = 215

cordelia_date = datetime.today().strftime('%y%m%d-%H%M')

memories = True

def make_json(dictonary, directory):
	for file_path in Path(directory).iterdir():
		if file_path.suffix == '.json':
			with open(file_path, 'r', encoding='utf-8') as f:
				dictonary[file_path.stem] = json.load(f)

cordelia_json = {}
make_json(cordelia_json, _PKG / 'config')

cordelia_alias = {}

with open(_PKG / 'config' / 'alias' / 'alias.json', 'r', encoding='utf-8') as f:
	cordelia_alias['alias'] = json.load(f)

with open(_PKG / 'config' / 'alias' / 'complex.json', 'r', encoding='utf-8') as f:
	cordelia_alias['complex'] = json.load(f)

