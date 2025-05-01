import numpy as np
from scipy.io.wavfile import write
from pathlib import Path
import struct
import pandas as pd
import os
import argparse
from datetime import datetime, timedelta

HIGH_SAMPLE_RATE = 8000  
LOW_SAMPLE_RATE = 1250  

def parse_timestamp_file(ts_file_path):
    """Parse the binary timestamp file into a list of timestamps"""
    timestamps = []
    
    with open(ts_file_path, 'rb') as f:
        while True:
            # Read a timestamp record (8 bytes: 4 for seconds, 2 for ms, 2 for buffer size, 1 for is_mono, 1 for padding)
            record = f.read(10) 
            if not record or len(record) < 10:
                break  
                
            # Unpack the timestamp data (little-endian format)
            # Format: <I (uint32) for seconds, <H (uint16) for milliseconds, 
            # <H (uint16) for buffer_byte_size, <B (uint8) for is_mono, <B (uint8) for reserved
            seconds, milliseconds, buffer_byte_size, is_mono, _ = struct.unpack('<IHHBB', record)
            
            timestamps.append({
                'seconds': seconds,
                'milliseconds': milliseconds,
                'buffer_byte_size': buffer_byte_size,
                'is_mono': bool(is_mono),
                'timestamp': seconds + milliseconds/1000.0
            })
    
    return timestamps

def generate_sample_timestamps(audio_data, sample_rate, timestamps):
    """Generate timestamps for each individual audio sample based on buffer timestamps"""
    
    ts_df = pd.DataFrame(timestamps)
    
    current_pos = 0
    sample_timestamps = []
    
    for i, ts_record in ts_df.iterrows():
        buffer_byte_size = ts_record['buffer_byte_size']
        is_mono = ts_record['is_mono']
        
        bytes_per_sample = 4 if sample_rate == HIGH_SAMPLE_RATE else 2
        
        bytes_per_frame = bytes_per_sample * (1 if is_mono else 2)
        
        buffer_frames = buffer_byte_size // bytes_per_frame
        
        if current_pos + buffer_frames > len(audio_data):
            buffer_frames = len(audio_data) - current_pos
            
        if buffer_frames <= 0:
            continue
            
        frame_duration = 1.0 / sample_rate
        
        buffer_start_time = ts_record['timestamp']
        
        for j in range(buffer_frames):
            sample_time = buffer_start_time + j * frame_duration
            sample_timestamps.append(sample_time)
            
        current_pos += buffer_frames
            
    if len(sample_timestamps) < len(audio_data):
        # If we have fewer timestamps than samples, extend using the last calculated interval
        last_interval = sample_duration
        last_time = sample_timestamps[-1]
        
        for i in range(len(audio_data) - len(sample_timestamps)):
            last_time += last_interval
            sample_timestamps.append(last_time)
    
    return sample_timestamps[:len(audio_data)]  # Truncate if needed

def write_csv_with_timestamps(audio_data, timestamps, output_file):
    """Write a CSV file with audio samples and their timestamps"""
    if len(audio_data.shape) > 1:  # Stereo
        df = pd.DataFrame({
            'timestamp': timestamps,
            'left_channel': audio_data[:, 0],
            'right_channel': audio_data[:, 1]
        })
    else:  # Mono
        df = pd.DataFrame({
            'timestamp': timestamps,
            'audio': audio_data
        })
    
    # Convert timestamps to datetime for readability
    base_time = datetime.fromtimestamp(timestamps[0])
    df['datetime'] = [base_time + timedelta(seconds=(t - timestamps[0])) for t in timestamps]
    
    df.to_csv(output_file, index=False)
    print(f"Saved timestamped audio data to {output_file}")

def main(input_folder, output_folder=None, csv_output=False):
    if output_folder is None:
        output_folder = input_folder
    else:
        os.makedirs(output_folder, exist_ok=True)
    
    data_folder = Path(input_folder)
    
    for path_raw_input in sorted(data_folder.iterdir()):
        # Process only audio files (without extensions)
        if (path_raw_input.is_file() and 
            path_raw_input.suffix == "" and
            ("MICLO" in path_raw_input.name or "MICHI" in path_raw_input.name)):

            print(f"Processing raw input file {path_raw_input}")

            path_wav_output = Path(output_folder) / (path_raw_input.name + ".wav")
            path_csv_output = Path(output_folder) / (path_raw_input.name + "_timestamped.csv")
            
            timestamp_file = path_raw_input.parent / (path_raw_input.name + ".D")
            has_timestamps = timestamp_file.exists()
            
            if has_timestamps:
                print(f"Found timestamp file: {timestamp_file}")
                timestamps = parse_timestamp_file(timestamp_file)
                print(f"Read {len(timestamps)} timestamp records")
            else:
                print(f"No timestamp file found for {path_raw_input}")
                timestamps = []

            if path_raw_input.stem[4:6] == "LO":
                sample_rate = LOW_SAMPLE_RATE
                buffer_dtype = np.int16  # 16-bit PCM
            elif path_raw_input.stem[4:6] == "HI":
                sample_rate = HIGH_SAMPLE_RATE
                buffer_dtype = np.int32  # 32-bit PCM
            else:
                print(f"Unknown sample rate identifier in filename: {path_raw_input.stem}")
                continue

            if path_raw_input.stem[0] == "0":
                num_channels = 2  # Stereo
            elif path_raw_input.stem[0] == "1":
                num_channels = 1  # Mono
            else:
                print(f"Unknown channel count identifier in filename: {path_raw_input.stem}")
                continue

            with path_raw_input.open("rb") as f:
                raw_data = f.read()
            
            audio_data = np.frombuffer(raw_data, dtype=buffer_dtype)

            if num_channels == 2:
                audio_data = audio_data.reshape(-1, 2)

            # Save the data in a WAV file
            write(filename=str(path_wav_output), rate=sample_rate, data=audio_data)
            print(f"Saved WAV file: {path_wav_output}")
            
            # Process timestamps if available and CSV output is requested
            if has_timestamps and csv_output:
                sample_timestamps = generate_sample_timestamps(audio_data, sample_rate, timestamps)
                write_csv_with_timestamps(audio_data, sample_timestamps, path_csv_output)

if __name__ == '__main__':
    """
    Parses audio files from the midge and creates WAV files.
    Also processes timestamp files to create CSV files with per-sample timestamps.
    """
    parser = argparse.ArgumentParser(description='Parser for audio data with timestamps from Mingle Midges')
    parser.add_argument('--input', required=True, help='Path to the input folder containing raw audio files')
    parser.add_argument('--output', required=False, help='Path to the output folder (default: same as input)')
    parser.add_argument('--csv', action='store_true', help='Generate CSV files with timestamped audio data')
    
    args = parser.parse_args()
    main(args.input, args.output, args.csv)
