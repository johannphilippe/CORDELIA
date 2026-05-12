import ctcsound
import subprocess
import shutil
import re
from pathlib import Path

from constants.var import cordelia_date, cordelia_given_instr
from constants.path import cordelia_score
from src.read_config import Main_config

# cordelia/csoundAPI/cs.py -> csoundAPI/ -> cordelia/
_PKG = Path(__file__).resolve().parent.parent

def remember(instrument_name):

	instr_add = (len(cordelia_given_instr))/10000
	instr_setting = f'schedule {round(945+instr_add, 5)}, 0, -1, "{instrument_name}", "{cordelia_score}/cor{cordelia_date}-{instrument_name}.wav"\n'
	return instr_setting

def csound_clear_instrument(instrument_name):
	
	instr_setting = []
	start = cordelia_nchnls * (len(cordelia_given_instr) - 1) + 1
	sequence = [start + i for i in range(cordelia_nchnls)]
	for index, val in enumerate(sequence):
		instr_num = 950 + (val/10000)
		instr_setting.append(f'schedule {round(instr_num, 5)}, 0, -1, "{instrument_name}_{index+1}"')
	return instr_setting

def create_dir(directory):
	Path(directory).mkdir(parents=True, exist_ok=True)
	print(f"Directory '{directory}' ready.")

# Extract the device name from the input string
def extract_device(input_string):
	start_index = input_string.find("(") + 1
	end_index = input_string.rfind(")") + 1
	return input_string[start_index:end_index]

# Return the -+rtaudio= option line from option.orc, or None if absent
def which_rtaudio():
	match = '-+rtaudio='
	with open(_PKG / 'csound_cordelia' / 'option.orc', encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if not line.startswith(';') and line.startswith(match):
				return line
	return None

# Get the list of devices and their details
def get_devices():
	rtaudio = which_rtaudio()
	# No rtaudio option → let Csound pick the default; JACK needs no -adc/-dac flags
	if rtaudio is None or rtaudio.lower() == '-+rtaudio=jack':
		return []
	csound = shutil.which('csound')
	if csound is None:
		raise RuntimeError("'csound' not found. Install Csound and ensure it is on your PATH.")
	output = subprocess.run([csound, rtaudio, '--devices'], capture_output=True, text=True).stderr.strip()
	devices = re.findall(r'adc.*|dac.*', output, flags=re.MULTILINE)
	return list(devices)

def process_line(line, converter, devices, options):
	for device in devices:
		if line in device:
			match = re.match(fr'{converter}\d+', device)
			if match:
				code = match.group(0)
				string = f'-i{code}' if converter == 'adc' else f'-o{code}'
				line_and_options = line.strip().split('--')
				if len(line_and_options) > 1:
					for opt in line_and_options[1:]:
						options.append(f'--{opt}')
				options.append(string)
				devices.remove(device)
				return True  # Return True if a match is found
	return False  # Return False if no match is found



# Query devices and construct the appropriate OPTIONs for ADC or DAC
def query_devices():
	rtaudio = which_rtaudio()

	# JACK manages its own port connections — no -adc/-dac flags needed.
	# Returning [] lets option.orc have full control (e.g. ;-iadc stays off).
	if rtaudio is None or rtaudio.lower() == '-+rtaudio=jack':
		return []

	devices = get_devices()
	options = []

	for converter in ['adc', 'dac']:
		with open(_PKG / 'default' / converter, encoding='utf-8') as f:
			for line in f.readlines():
				line_and_options = line.strip().split('--')
				line = line_and_options[0]
				if line and not line.startswith(';'):
					match_found = False
					for device in devices:
						if line in device:
							match = re.match(fr'{converter}\d+', device)
							if match:
								code = match.group(0)
								string = f'-i{code}' if converter == 'adc' else f'-o{code}'
								if len(line_and_options) > 1:
									for opt in line_and_options[1:]:
										options.append(f'--{opt}')
								options.append(string)
								devices.remove(device)
								match_found = True
								break
					if match_found:
						break

	# Non-JACK fallback: output only (-odac); don't force input since most
	# live-coding setups don't need ADC and forcing it can crash Csound.
	return options if options else ['-odac']

def init_csound():
	OPTIONs = []

	with open(_PKG / 'csound_cordelia' / 'option.orc', encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if line and not line.startswith(';'):
				OPTIONs.append(line)

	OPTIONs.extend(query_devices())
	OPTIONs.append(f'--nchnls={CORDELIA_CONFIG.nchnls}')

	print('···last options:')
	for option in OPTIONs:
		csound_cordelia.setOption(option)
		print(option)

	SETTINGs = []
	SETTINGs.append(f'ginchnls init {CORDELIA_CONFIG.csound_audio_array_count}')
	with open(_PKG / 'csound_cordelia' / 'setting.orc', encoding='utf-8') as f:
		SETTINGs.append(f.read())

	with open(_PKG / 'csound_cordelia' / 'include.orc', encoding='utf-8') as f:
		SETTINGs.append(f.read())

	csound_cordelia.compileOrcAsync('\n'.join(SETTINGs))
	print('\n'.join(SETTINGs))
#######################################
# INIT CSOUND OPTIONs
#######################################
ctcsound.csoundInitialize(ctcsound.CSOUNDINIT_NO_ATEXIT | ctcsound.CSOUNDINIT_NO_SIGNAL_HANDLER)
csound_cordelia = ctcsound.Csound()

CORDELIA_CONFIG = Main_config()

init_csound()

cordelia_nchnls = CORDELIA_CONFIG.csound_audio_array_count
print(f'Cordelia has {cordelia_nchnls} channels\n')

cordelia_sr = int(csound_cordelia.sr())
print(f'Cordelia has a sample rate of {cordelia_sr}\n')

cordelia_ksmps = int(csound_cordelia.ksmps())
print(f'Cordelia has {cordelia_ksmps} ksmps\n')
