import sys
from pathlib import Path

# cordelia/script/main_script.py -> script/ -> cordelia/
_SCRIPT_DIR = Path(__file__).resolve().parent
_PKG_DIR    = _SCRIPT_DIR.parent

sys.path.insert(0, str(_SCRIPT_DIR))  # for `make` package
sys.path.insert(0, str(_PKG_DIR))     # for `constants` package

from make import include, gen, instr, routing, scala, tokens
from constants.path import CORDELIA_ROOT, CORDELIA_PKG

include_dir = CORDELIA_PKG / 'csound_cordelia'
include_orc = include_dir / 'include.orc'

gen_dir  = CORDELIA_ROOT / '_GEN'
gen_json = CORDELIA_PKG / 'config' / 'GEN.json'

instr_dir  = CORDELIA_ROOT / '_INSTR'
instr_json = CORDELIA_PKG / 'config' / 'INSTR.json'

routing_dir  = CORDELIA_ROOT / '_MOD'
routing_json = CORDELIA_PKG / 'config' / 'ROUTING.json'
routing_orc  = CORDELIA_PKG / 'csound_cordelia' / '3-body' / '3-MOD.orc'

scala_dir  = CORDELIA_ROOT / '_SCALA'
scala_json = CORDELIA_PKG / 'config' / 'SCALA.json'

tokens_json = CORDELIA_PKG / 'config' / 'tokens.json'

def main():

	print('Processing INCLUDE')
	include.make(include_orc, include_dir)
	
	print('Processing GEN')
	gen.make(gen_dir, gen_json)

	print('Processing INSTR')
	instr.make(instr_dir, instr_json)

	print('Processing ROUTING')
	routing.make(routing_orc, routing_dir, routing_json)
	
	print('Processing SCALA')
	scala.make(scala_dir, scala_json)

	print('Processing TOKENs')
	tokens.make(routing_json, tokens_json)

if __name__ == "__main__":
	main()