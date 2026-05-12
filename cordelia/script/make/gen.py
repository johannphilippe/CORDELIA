import json
from pathlib import Path

def make(directory, json_file):
	gen = {}
	for p in Path(directory).rglob('*.orc'):
		with open(p, 'r', encoding='utf-8') as f:
			gen[p.stem] = f.read()

	with open(json_file, 'w', encoding='utf-8') as f:
		json.dump(gen, f, indent=4)

