#!/usr/bin/env python

import numpy as np
from scipy.io.wavfile import write
from pathlib import Path
import struct
from parser_utilities import parse_timestamps
import os
from tqdm import tqdm

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

def decode_audio_file(path_raw_input):
    """
    Decode a single audio file and save as WAV.
    
    Args:
        path_raw_input: Path to the raw audio file
    """
    if not (path_raw_input.is_file() and path_raw_input.suffix == "" and
            ("MICLO" in path_raw_input.stem or "MICHI" in path_raw_input.stem)):
        return
    
    print("Audio input file " + str(path_raw_input))
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

def read_int64_little_endian(file_path):
    results = []
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(8)
            if len(chunk) < 8:
                break  # End of file
            value = struct.unpack('<q', chunk)[0]  # '<q' = little-endian signed int64
            results.append(value)
    return results

def decode_timestamp_file(path_input):
    """
    Decode a single timestamp file (.D file) and save results as -ts files with datetime format.
    """
    if not (path_input.is_file() and path_input.suffix == ".D"):
        return
        
    print("Timestamp input file " + str(path_input))
    path_output = path_input.parent / (path_input.stem + "-ts.txt")
    try:
        timestamp_data = read_int64_little_endian(path_input)
        # Convert timestamps to datetime format
        datetime_data = parse_timestamps(timestamp_data, str(path_input))
        # Save the datetime data as a text file with one datetime per line
        with path_output.open("w") as f:
            for datetime_val in datetime_data:
                f.write("{}\n".format(datetime_val))
        print("Successfully decoded {} timestamps to {}".format(len(datetime_data), path_output))
    except Exception as e:
        print("Error processing {}: {}".format(path_input, e))

def process_input_file(input_path):
    # Process audio files
    if input_path.is_file() and input_path.suffix == "" and ("MICLO" in input_path.stem or "MICHI" in input_path.stem):
        decode_audio_file(input_path)
    # Process timestamp files
    elif input_path.is_file() and input_path.suffix == ".D":
        decode_timestamp_file(input_path)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parser for the audio data and timestamps obtained from Mingle Midges')
    parser.add_argument('--fn', required=True, help='Please enter the path to the folder')
    args = parser.parse_args()

    input_dir = args.fn
    for root_str, _, files in tqdm(list(os.walk(input_dir)), desc="Files"):
        root = Path(root_str)
        for filename in files:
            input_path = root / filename
            process_input_file(input_path)
