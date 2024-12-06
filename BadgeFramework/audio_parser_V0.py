import numpy as np
from scipy.io.wavfile import write
from pathlib import Path
import argparse
import os

HIGH_SAMPLE_RATE = 8000
LOW_SAMPLE_RATE = 1250
EMPIRICAL_RATE = 5000
# s_rate = 5000
audio_file_name_elements = ['MICLO', 'MICHI', 'audio']

def process_audio_file(path_raw_input, low_sample_rate, high_sample_rate):
    """
    Process a single audio file, converting raw data into a WAV file with appropriate sample rate and channels.
    """
    # Determine output path

    # Determine sample rate based on filename
    # sample_rate = determine_sample_rate(path_raw_input.stem, low_sample_rate, high_sample_rate)
    # num_channels = determine_num_channels(path_raw_input.stem)

    sample_rate = EMPIRICAL_RATE
    num_channels = 1
    path_wav_output = path_raw_input.parent / (path_raw_input.stem + f"_{sample_rate}.wav")

    # Read raw data
    with path_raw_input.open("rb") as f:
        raw_data = f.read()

    # Convert raw data to numpy array
    audio_data = np.frombuffer(raw_data, dtype=np.int32)
    if num_channels == 2:
        audio_data = audio_data.reshape(-1, 2)

    # Upsample if necessary
    if sample_rate == low_sample_rate:
        audio_data = upsample_audio(audio_data, low_sample_rate, high_sample_rate, num_channels)

    # Save as WAV file
    save_audio_as_wav(path_wav_output, sample_rate, audio_data)


def determine_sample_rate(stem, low_sample_rate, high_sample_rate):
    """
    Determine the sample rate based on the filename stem.
    """
    if "LO" in stem:
        return low_sample_rate
    elif "HI" in stem:
        return high_sample_rate
    else:
        raise RuntimeError("Unknown sample rate type in filename")


def determine_num_channels(stem):
    """
    Determine the number of audio channels based on the filename stem.
    """
    if stem[0] == "0":
        return 2  # Stereo
    elif stem[0] == "1":
        return 1  # Mono
    else:
        raise RuntimeError("Unknown number of channels")


def upsample_audio(audio_data, low_sample_rate, high_sample_rate, num_channels):
    """
    Upsample audio data from a lower sample rate to a higher sample rate using linear interpolation.
    """
    xp = np.linspace(0, audio_data.shape[0], audio_data.shape[0])
    x = np.linspace(0, audio_data.shape[0], int(audio_data.shape[0] * (high_sample_rate / low_sample_rate)))

    if num_channels == 1:
        return np.interp(x, xp, audio_data)
    else:
        fp0 = np.interp(x, xp, audio_data[:, 0])
        fp1 = np.interp(x, xp, audio_data[:, 1])
        return np.stack([fp0, fp1], axis=1)


def save_audio_as_wav(output_path, sample_rate, audio_data):
    """
    Save audio data to a WAV file.
    """
    write(filename=str(output_path), rate=sample_rate, data=audio_data)


def is_audio_file_name(name):
    for x in audio_file_name_elements:
        if x in name:
            return True
    return False

def deal_audio(fn):
    """
    Process all valid audio files in a directory.
    """
    data_folder = Path(fn)
    for path_raw_input in sorted(data_folder.iterdir()):
        print(path_raw_input, path_raw_input.suffix == "")
        if (
            path_raw_input.is_file()
            and path_raw_input.suffix == ""
            and is_audio_file_name(path_raw_input.stem)
        ):
            process_audio_file(path_raw_input, LOW_SAMPLE_RATE, HIGH_SAMPLE_RATE)

def get_kth_latest(folder_path, k=1):
    """
    Get the path of the k-th largest subfolder based on 'y' in the subfolder names 'x_y'.

    Args:
        folder_path (str): Path to the main folder containing subfolders named 'x_y'.
        k (int): The rank of the subfolder to retrieve (1-based).

    Returns:
        str: Path of the k-th largest subfolder based on 'y'.

    Raises:
        ValueError: If 'k' is invalid or there are not enough valid subfolders.
    """
    # List to store subfolders with extracted y-values
    subfolders_with_y = []

    # Iterate over subfolders
    for subfolder in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path):
            # Split subfolder name into x and y
            try:
                x, y = subfolder.split('_')
                y = int(y)  # Convert y to an integer
                subfolders_with_y.append((y, subfolder_path))
            except (ValueError, IndexError):
                # Skip subfolders that don't match the 'x_y' pattern
                pass

    # Sort subfolders by y in descending order
    subfolders_with_y.sort(reverse=True, key=lambda item: item[0])

    # Validate k
    if k < 1 or k > len(subfolders_with_y):
        raise ValueError(f"Invalid value of k: {k}. Must be between 1 and {len(subfolders_with_y)}.")

    # Return the path of the k-th largest subfolder
    return subfolders_with_y[k - 1][1]


def main():
    """
        Takes as input a folder with RAW audio files from the midge and saves them as .wav files.
        """
    # parser = argparse.ArgumentParser(description='Parser for the audio data obtained from Mingle Midges')
    # parser.add_argument('--fn', required=True, help='Please enter the path to the file')
    # args = parser.parse_args()
    midge_data_parent = "/home/zonghuan/tudelft/projects/datasets/new_collection/tech_pilot_1/midge_data/"
    midge_id = 54
    midge_folder = get_kth_latest(os.path.join(midge_data_parent, str(midge_id)), 1)
    deal_audio(fn=midge_folder)
    # add something at home


if __name__ == '__main__':
    main()

# import numpy as np
# from scipy.io.wavfile import write
# from pathlib import Path
#
# HIGH_SAMPLE_RATE = 8000
# LOW_SAMPLE_RATE = 1250
#
#
# def main(fn):
#     data_folder = Path(fn)
#     for path_raw_input in sorted(data_folder.iterdir()):
#         if (path_raw_input.is_file() and path_raw_input.suffix == "" and
#                 ("MICLO" in path_raw_input.stem or "MICHI" in path_raw_input.stem)):
#
#             print("Raw input file " + str(path_raw_input))
#
#             path_wav_output = path_raw_input.parent / (path_raw_input.stem + ".wav")
#
#             if path_raw_input.stem[4:6] == "LO":
#                 sample_rate = LOW_SAMPLE_RATE  # Low frequency sampling
#                 buffer_dtype = np.int16  # 16-bit PCM
#             elif path_raw_input.stem[4:6] == "HI":
#                 sample_rate = HIGH_SAMPLE_RATE  # High frequency sampling
#                 buffer_dtype = np.int32  # 32-bit PCM
#             else:
#                 raise RuntimeError("Unknown number of channels")
#
#             if path_raw_input.stem[0] == "0":
#                 num_channels = 2  # Stereo
#             elif path_raw_input.stem[0] == "1":
#                 num_channels = 1  # Mono
#             else:
#                 raise RuntimeError("Unknown number of channels")
#
#             with path_raw_input.open("rb") as f:
#                 raw_data = f.read()
#
#             audio_data = np.frombuffer(raw_data, dtype=buffer_dtype)
#
#             if num_channels == 2:
#                 audio_data = audio_data.reshape(-1, 2)
#
#             # Save the data in a WAV file
#             write(filename=str(path_wav_output), rate=sample_rate, data=audio_data)
#
#
# if __name__ == '__main__':
#     """
#     Takes as input a folder with RAW audio files from the midge and saves them as .wav files.
#     """
#     import argparse
#
#     parser = argparse.ArgumentParser(description='Parser for the audio data obtained from Mingle Midges')
#     parser.add_argument('--fn', required=True, help='Please enter the path to the file')
#     args = parser.parse_args()
#     main(fn=args.fn)
