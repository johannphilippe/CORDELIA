import sys, math, shutil
from pathlib import Path
import abjad

# rpr/_lilypond-def/txt2ly.py -> _lilypond-def/
LILYPOND_SETTING_DEFAULT = Path(__file__).resolve().parent / 'pre.ly'

def fetch_instr_names(file):
	
	instr_names = set()
	
	with open(file, 'r', encoding='utf-8') as f:
		for line in f:
			start_index = line.find('"') + 1
			end_index = line.find('"', start_index)
			instr_names.add(line[start_index:end_index])
	
	return instr_names

def add_string_for_each_name(instr_name):
	lilypond_space_string = f"\\new Staff = {instr_name}" + " " + "\\repeat unfold 16 { s1 \\break }"
	return lilypond_space_string


def convert_each_line(file):	
	lines = []
	with open(file, 'r', encoding='utf-8') as f:
		for line in f:
			#"bass", 0.0, 0.2789473684210526, 0.0146484375, giclassic, 1825.18519
			name, start, dur, dyn, env, freq = line.split(', ')

			name = name.replace('"', '')
			start = round(float(dur), 3)
			dur = round(float(dur), 3)
			pitch = abjad.NamedPitch.from_hertz(float(freq)).get_name()
			if pitch.startswith('bf'):
				pitch = "f'"
			
			#\at regan ##e14.87 b' ##e1 "-35.18¢" "14.87s"
			lilypond_string = f'\\at {name} ##e{start} {pitch} ##e{dur} "0¢" "{start}s"'
			lines.append(lilypond_string)
	return lines



for file in sys.argv[1:]:

	basename = Path(file).stem
	dir_path = str(Path(file).parent)

	lines = []

	for i in fetch_instr_names(file):
		lines.append(add_string_for_each_name(i))
	
	lines.extend(convert_each_line(file))

	output = Path(file).parent / (basename + '.ly')
	shutil.copy2(LILYPOND_SETTING_DEFAULT, output)
	with open(output, 'a', encoding='utf-8') as f:

		f.write('\n<<\n')
		f.write('\n'.join(lines))
		f.write('\n>>\n')
