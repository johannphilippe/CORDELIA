from pathlib import Path

def make(orc, directory):
	excluded = {'option', 'include', 'setting'}
	includes = sorted(
		f'"{p}"'
		for p in Path(directory).rglob('*.orc')
		if p.stem not in excluded
	)
	includes = ['#include ' + item for item in includes]

	with open(orc, 'w', encoding='utf-8') as include_file:
		include_file.write('\n'.join(includes))

