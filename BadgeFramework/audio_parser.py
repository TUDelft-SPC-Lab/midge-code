#!/usr/bin/env python

import numpy as np
from scipy.io.wavfile import write
from pathlib import Path
import struct

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

def decode_audio(fn):
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

def decode_timestamp(fn):
    """
    Decode timestamp files (.D files) in the given folder and save results as -ts files.
    
    Args:
        fn (str): Path to the folder containing .D files
    """
    data_folder = Path(fn)
    for path_input in sorted(data_folder.iterdir()):
        if (path_input.is_file() and path_input.suffix == ".D"):
            print("Timestamp input file " + str(path_input))
            
            path_output = path_input.parent / (path_input.stem + "-ts.txt")
            
            try:
                timestamp_data = read_int64_little_endian(path_input)
                
                # Save the timestamp data as a text file with one timestamp per line
                with path_output.open("w") as f:
                    for timestamp in timestamp_data:
                        f.write(f"{timestamp}\n")
                
                print(f"Successfully decoded {len(timestamp_data)} timestamps to {path_output}")
                
            except Exception as e:
                print(f"Error processing {path_input}: {e}")


def process_all_subfolders(parent_folder, processing_type='audio'):
    """
    Process all subfolders in the given parent folder by calling the appropriate decode function for each subfolder.
    
    Args:
        parent_folder (str): Path to the parent folder containing subfolders to process
        processing_type (str): Type of processing - 'audio' or 'timestamp'
    """
    parent_path = Path(parent_folder)
    
    if not parent_path.exists():
        raise FileNotFoundError(f"Parent folder '{parent_folder}' does not exist")
    
    if not parent_path.is_dir():
        raise NotADirectoryError(f"'{parent_folder}' is not a directory")
    
    subfolders = [item for item in parent_path.iterdir() if item.is_dir()]
    
    if not subfolders:
        print(f"No subfolders found in '{parent_folder}'")
        return
    
    print(f"Found {len(subfolders)} subfolders to process:")
    for subfolder in subfolders:
        print(f"  - {subfolder.name}")
    
    # Choose the appropriate decode function based on processing type
    if processing_type == 'audio':
        decode_func = decode_audio
    elif processing_type == 'timestamp':
        decode_func = decode_timestamp
    else:
        raise ValueError(f"Unknown processing type: {processing_type}. Must be 'audio' or 'timestamp'")
    
    for subfolder in sorted(subfolders):
        print(f"\nProcessing subfolder: {subfolder.name}")
        try:
            decode_func(str(subfolder))
            print(f"Successfully processed: {subfolder.name}")
        except Exception as e:
            print(f"Error processing {subfolder.name}: {e}")


if __name__ == '__main__':
    """
    Takes as input a folder with RAW audio files from the midge and saves them as .wav files,
    or decodes timestamp files (.D files) and saves them as text files.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Parser for the audio data and timestamps obtained from Mingle Midges')
    parser.add_argument('--fn', required=True, help='Please enter the path to the file or folder')
    parser.add_argument('--subfolders', action='store_true', help='Process all subfolders in the given folder instead of the folder itself')
    parser.add_argument('--mode', choices=['audio', 'timestamp'], required=True, help='Mode: "audio" to decode audio files, "timestamp" to decode timestamp files')
    args = parser.parse_args()
    
    if args.mode == 'audio':
        if args.subfolders:
            process_all_subfolders(args.fn, 'audio')
        else:
            decode_audio(fn=args.fn)
    elif args.mode == 'timestamp':
        if args.subfolders:
            process_all_subfolders(args.fn, 'timestamp')
        else:
            decode_timestamp(args.fn)

