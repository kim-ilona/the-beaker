import noisereduce as nr
import soundfile as sf
import sys

input_path = sys.argv[1]
output_path = sys.argv[2]

data, rate = sf.read(input_path)
reduced = nr.reduce_noise(y=data, sr=rate, prop_decrease=0.6)
sf.write(output_path, reduced, rate)
print(f"[denoised] {output_path}")
