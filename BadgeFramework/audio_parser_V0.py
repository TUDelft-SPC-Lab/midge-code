import argparse
import wave

import numpy as np
from scipy.io.wavfile import write
from pathlib import Path

HIGH_SAMPLE_RATE = 8000
LOW_SAMPLE_RATE = 1250


def parse_folder(fn):
    data_folder = Path(fn)
    for path_raw_input in sorted(data_folder.iterdir()):
        if (path_raw_input.is_file() and path_raw_input.suffix == "" and
            ("MICLO" in path_raw_input.stem or "MICHI" in path_raw_input.stem)):

            print("Raw input file " + str(path_raw_input))

            path_wav_output = path_raw_input.parent / (path_raw_input.stem + ".wav")

            if path_raw_input.stem[4:6] == "LO":
                sample_rate = LOW_SAMPLE_RATE  # Low frequency sampling
                buffer_dtype = np.int16 # 16-bit PCM
            elif path_raw_input.stem[4:6] == "HI":
                sample_rate = HIGH_SAMPLE_RATE  # High frequency sampling
                buffer_dtype = np.int32 # 32-bit PCM
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


def parse_simple(path_raw_input: Path, path_wav_output: Path):
    sample_rate = 20000  # Low frequency sampling
    buffer_dtype = np.int16  # 16-bit PCM
    num_channels = 1  # Mono

    with path_raw_input.open("rb") as f:
        raw_data = f.read()

    audio_data = np.frombuffer(raw_data, dtype=buffer_dtype)
    if num_channels == 2:
        audio_data = audio_data.reshape(-1, 2)

    # Save the data in a WAV file
    write(filename=str(path_wav_output), rate=sample_rate, data=audio_data)


def get_wav_info(file_path: Path):
    """Extracts metadata and raw audio data from a WAV file."""
    try:
        with wave.open(str(file_path), 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)
            dtype = np.int16 if params.sampwidth == 2 else np.int32
            audio_data = np.frombuffer(frames, dtype=dtype)
            if params.nchannels == 2:
                audio_data = audio_data.reshape(-1, 2)

            info = {
                "Channels": params.nchannels,
                "Sample Width (bytes)": params.sampwidth,
                "Frame Rate (Hz)": params.framerate,
                "Number of Frames": params.nframes,
                "Compression Type": params.comptype,
                "Compression Name": params.compname,
                "Duration (s)": params.nframes / params.framerate,
                "Audio Data": audio_data
            }
            return info
    except wave.Error as e:
        print(f"Error reading {file_path}: {e}")
        return None


def compare_wav_files(file1, file2):
    """Compares two WAV files and prints their differences, including audio data analysis."""
    info1 = get_wav_info(file1)
    info2 = get_wav_info(file2)

    if not info1 or not info2:
        print("One or both files could not be read correctly.")
        return

    print("Comparison of WAV Files:")
    print(f"{'Attribute':<25}{'File 1':<20}{'File 2'}")
    print("-" * 65)
    for key in info1:
        if key != "Audio Data":
            value1 = info1[key]
            value2 = info2[key]
            match = "✔" if value1 == value2 else "✘"
            print(f"{key:<25}{str(value1):<20}{str(value2)}  {match}")

    # Compare actual audio data
    audio_data1 = info1["Audio Data"]
    audio_data2 = info2["Audio Data"]

    min_length = min(len(audio_data1), len(audio_data2))
    if min_length == 0:
        print("Cannot compare empty audio data.")
        return

    audio_data1 = audio_data1[:min_length]
    audio_data2 = audio_data2[:min_length]

    diff = audio_data1 - audio_data2
    max_diff = np.max(np.abs(diff))
    norm_diff = np.linalg.norm(diff)

    print("\nAudio Data Comparison:")
    print(f"Max Difference: {max_diff}")
    print(f"Norm of Difference: {norm_diff}")


if __name__ == '__main__':
    """
    Takes as input a folder with RAW audio files from the midge and saves them as .wav files.
    """
    # import argparse
    # parser = argparse.ArgumentParser(description='Parser for the audio data obtained from Mingle Midges')
    # parser.add_argument('--fn', required=True,help='Please enter the path to the file')
    # args = parser.parse_args()
    # parse_folder(fn=args.fn)

    # 1587563550840_audio_2, 1587564263795_audio_2, 1587564858250_audio_2
    stephanie_path = Path("C:\\Users\\zongh\\OneDrive - Delft University of Technology\\tudelft\\projects\\"
                          "dataset_collection\\sync-experiments\\artefacts\\av_data\\midge\\15\\1587564858250_audio_2")
    pilot1_path = Path("C:\\Users\\zongh\\OneDrive - Delft University of Technology\\tudelft\\projects\\"
                       "dataset_collection\\sync-experiments\\artefacts\\av_data\\midge\\15\\1587564858250_audio_2")
    output_path = Path("C:\\Users\\zongh\\OneDrive - Delft University of Technology\\tudelft\\projects\\"
                       "dataset_collection\\tech_pilot_1\\audio_test")

    old_wav_path = Path("C:\\Users\\zongh\\OneDrive - Delft University of Technology\\tudelft\\projects\\"
                        "dataset_collection\\sync-experiments\\artefacts\\av_data\\midge\\15\\1587564858250.wav")

    new_wav_path = output_path / (pilot1_path.stem + "_py.wav")

    parse_simple(pilot1_path, new_wav_path)
    # compare_wav_files(old_wav_path, new_wav_path)
