import os
import tempfile

output_tempdir = tempfile.gettempdir()
input_file_wav = '/Users/j/Desktop/dp-glued.wav'
basename = os.path.splitext(os.path.basename(input_file_wav))[0]

for f in os.listdir(output_tempdir):
    if f.endswith('.ats') and basename in f:
        print(f)
        #os.remove(f)
