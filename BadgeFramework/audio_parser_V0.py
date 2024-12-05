import numpy as np
from numpy.random import random
from scipy.io.wavfile import write
from pathlib import Path
import argparse
import os

HIGH_SAMPLE_RATE = 8000
LOW_SAMPLE_RATE = 1250
s_rate = 5000

def deal_audio(fn):
    data_folder = Path(fn)
    for path_raw_input in sorted(data_folder.iterdir()):
        print(path_raw_input, path_raw_input.suffix == "")
        if (path_raw_input.is_file() and path_raw_input.suffix == "" and
                ("MICLO" in path_raw_input.stem or "MICHI" in path_raw_input.stem or "audio" in path_raw_input.stem)):

            path_wav_output = path_raw_input.parent / (path_raw_input.stem + f"_{s_rate}.wav")

            # if path_raw_input.stem[4:6] == "LO":
            #     sample_rate = LOW_SAMPLE_RATE  # Low frequency sampling
            #     raise NotImplementedError("Low sample rate does not work yet")
            # elif path_raw_input.stem[4:6] == "HI":
            #     sample_rate = HIGH_SAMPLE_RATE  # High frequency sampling
            # else:
            #     raise RuntimeError("Unknown number of channels")
            #
            # if path_raw_input.stem[0] == "0":
            #     num_channels = 2  # Stereo
            # elif path_raw_input.stem[0] == "1":
            #     num_channels = 1  # Mono
            # else:
            #     raise RuntimeError("Unknown number of channels")

            sample_rate = HIGH_SAMPLE_RATE
            num_channels = 2
            with path_raw_input.open("rb") as f:
                raw_data = f.read()

            # 32-bit PCM uses numpy dtype int32
            audio_data = np.frombuffer(raw_data, dtype=np.int32)

            if num_channels == 2:
                audio_data = audio_data.reshape(-1, 2)

            # Upsample the low sample rate to high sample rate by linear interpolation
            if sample_rate == LOW_SAMPLE_RATE:
                xp = np.linspace(0, audio_data.shape[0], audio_data.shape[0])
                x = np.linspace(0, audio_data.shape[0], audio_data.shape[0] * (HIGH_SAMPLE_RATE / LOW_SAMPLE_RATE))
                if num_channels == 1:
                    audio_data = np.interp(x, xp, audio_data)
                else:
                    fp0 = np.interp(x, xp, audio_data[:, 0])
                    fp1 = np.interp(x, xp, audio_data[:, 1])
                    audio_data = np.stack([fp0, fp1], axis=1)

                print(audio_data.shape)

            # Save the audio data as a WAV file
            write(filename=str(path_wav_output), rate=s_rate, data=audio_data)


def main():
    """
        Takes as input a folder with RAW audio files from the midge and saves them as .wav files.
        """
    # parser = argparse.ArgumentParser(description='Parser for the audio data obtained from Mingle Midges')
    # parser.add_argument('--fn', required=True, help='Please enter the path to the file')
    # args = parser.parse_args()
    midge_id = 54
    midge_folder = os.path.join('/home/zonghuan/tudelft/projects/datasets/new_collection/tech_pilot_1/midge_data/',
                                str(midge_id), '65535_1730466472')
    deal_audio(fn=midge_folder)


if __name__ == '__main__':
    main()


