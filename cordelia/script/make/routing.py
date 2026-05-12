import json
import re
from pathlib import Path

def extract_text(text, section):
	start = fr';START {section}\s'
	end = fr';END {section}\s'
	match = re.search(f'{start}(.*?){end}', text, re.DOTALL)
	if match:
		return match.group(1).strip()

def make(orc_file, directory, json_file):
	modules = {}
	for p in Path(directory).iterdir():
		if p.suffix == '.orc':
			with open(p, 'r', encoding='utf-8') as file:
				text = file.read() + '\n'

			modules[p.stem] = {
				'input':  extract_text(text, 'INPUT'),
				'core':   extract_text(text, 'CORE'),
				'opcode': extract_text(text, 'OPCODE'),
			}

	modules = dict(sorted(modules.items()))
	with open(json_file, 'w', encoding='utf-8') as f:
		json.dump(modules, f, indent=4)
