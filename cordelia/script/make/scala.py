import re
import json
from pathlib import Path

# scala.py -> make/ -> script/ -> cordelia/ -> project root
_ROOT = Path(__file__).resolve().parent.parent.parent.parent

def find_duplicate_files(directory):
	file_dict = {}

	for p in Path(directory).rglob('*.scl'):
		if p.stem in file_dict:
			file_dict[p.stem].append(p)
		else:
			file_dict[p.stem] = [p]

	duplicates = {stem: paths for stem, paths in file_dict.items() if len(paths) > 1}

	if not duplicates:
		print("No duplicate files found.")
		return True
	else:
		print("Duplicate files found:")
		for stem, paths in duplicates.items():
			print(f"File '{stem}' is duplicated at:")
			for path in paths:
				print(f"  {path}")
		return False

def find_nonstandard_names(directory):
	for p in Path(directory).rglob('*.scl'):
		if re.search(r'\s', p.name):
			print(p)
			return False
	return True

def round_large_integer(number):
	number = int(number)
	max_64bit_int = 2 ** 63 - 1  # Maximum 64-bit signed integer
	if number > max_64bit_int:
		rounded_number = round(number, -15)  # Round to 15 significant digits
		return rounded_number
	else:
		return number

def process_scala(directory, json_file):
	scala = {}

	for p in Path(directory).rglob('*.scl'):
		with open(p, 'r', encoding='latin1') as f:
			lines = [line.strip() for line in f if not line.strip().startswith('!')]

		description = lines[0] if lines[0] != '' else None
		degrees = lines[1].split()[0]

		tuning_value = []
		for value in lines[2:]:
			value = value.split('!')[0]

			if '(' in value:
				res = value
			elif '/' in value:
				components = [str(round_large_integer(c)) for c in value.split('/')]
				res = '/'.join(components)
			else:
				res = str(2 ** (float(value.split()[0]) / 1200))

			tuning_value.append(str(res))

		interval = tuning_value[-1]

		if degrees != str(len(tuning_value)):
			print('WARNING --- degrees are different from the tuning values')

		base_val = '1'
		basefreq = 'A4'
		basekey = '69'

		ftgen_string = f'gi{p.stem} ftgen 0, 0, 0, -2, {degrees}, {interval}, {basefreq}, {basekey}, {base_val}, {", ".join(tuning_value)}'
		scala[p.stem] = {
			'path': str(p.relative_to(_ROOT)),
			'description': description,
			'default_ftgen': ftgen_string,
			'degrees': degrees,
			'interval': interval,
			'tuning_values': ", ".join(tuning_value)
		}

	with open(json_file, 'w', encoding='utf-8') as f:
		json.dump(scala, f, indent=4)
	return True

def make(scala_dir, scala_json):
    ret = find_duplicate_files(scala_dir)
    if ret:
        ret = find_nonstandard_names(scala_dir)
    if ret:
        ret = process_scala(scala_dir, scala_json)
