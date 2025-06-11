#!/usr/bin/env python

import numpy as np
from scipy.io.wavfile import write
from pathlib import Path

PDM_CRYSTAL_CLK = 32e6 # Frequency that feeds the PDM clock generator
PDM_TO_PCM_DIV = 64 # https://docs.nordicsemi.com/bundle/ps_nrf52832/page/pdm.html#d931e120

#PDM clock variants taken from https://docs.nordicsemi.com/bundle/ps_nrf52832/page/pdm.html#d931e3773
#PDM_CLK_DIV = 30 # (1.067 MHz CLK variant)
#PDM_CLK_DIV = 31 # (1.032 MHz CLK variant)
#PDM_CLK_DIV = 32 # (1 MHz CLK variant)
PDM_CLK_DIV = 25 # (1.280 MHz CLK variant)

HIGH_SAMPLE_RATE = int((PDM_CRYSTAL_CLK / PDM_CLK_DIV) / PDM_TO_PCM_DIV)

# In LOW mode the midge will store one sample per DECIMATION samples
DECIMATION = 16
LOW_SAMPLE_RATE = int(HIGH_SAMPLE_RATE/DECIMATION)

def main(fn):
    data_folder = Path(fn)
    for path_raw_input in sorted(data_folder.iterdir()):
        if (path_raw_input.is_file() and path_raw_input.suffix == "" and
            ("MICLO" in path_raw_input.stem or "MICHI" in path_raw_input.stem)):

            print("Raw input file " + str(path_raw_input))

            path_wav_output = path_raw_input.parent / (path_raw_input.stem + ".wav")

            buffer_dtype = np.int16 # 16-bit PCM
            if path_raw_input.stem[4:6] == "LO":
                sample_rate = LOW_SAMPLE_RATE  # Low frequency sampling
            elif path_raw_input.stem[4:6] == "HI":
                sample_rate = HIGH_SAMPLE_RATE  # High frequency sampling
            else:
                raise RuntimeError("Unknown number of channels")

            if path_raw_input.stem[0] == "0":
                num_channels = 2  # Stereo
            elif path_raw_input.stem[0] == "1":
                num_channels = 1  # Mono
            else:
                raise RuntimeError("Unknown number of channels")

            with path_raw_input.open("rb") as f:
                raw_data = f.read()
            
            audio_data = np.frombuffer(raw_data, dtype=buffer_dtype)

            if num_channels == 2:
                audio_data = audio_data.reshape(-1, 2)

            # Save the data in a WAV file
            write(filename=str(path_wav_output), rate=sample_rate, data=audio_data)


if __name__ == '__main__':
    """
    Takes as input a folder with RAW audio files from the midge and saves them as .wav files.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Parser for the audio data obtained from Mingle Midges')
    parser.add_argument('--fn', required=True,help='Please enter the path to the file')
    args = parser.parse_args()
    main(fn=args.fn)

