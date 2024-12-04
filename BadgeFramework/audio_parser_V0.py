import numpy as np
from scipy.io.wavfile import write
from pathlib import Path

HIGH_SAMPLE_RATE = 8000
LOW_SAMPLE_RATE = 1250

def main(fn):
    data_folder = Path(fn)
    for path_raw_input in sorted(data_folder.iterdir()):
        if (path_raw_input.is_file() and path_raw_input.suffix == "" and
            ("MICLO" in path_raw_input.stem or "MICHI" in path_raw_input.stem)):

            print("Raw input file " + str(path_raw_input))

            path_wav_output = path_raw_input.parent / (path_raw_input.stem + ".wav")

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

            # Save the audio data as a WAV file
            write(filename=str(path_wav_output), rate=HIGH_SAMPLE_RATE, data=audio_data)


if __name__ == '__main__':
    """
    Takes as input a folder with RAW audio files from the midge and saves them as .wav files.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Parser for the audio data obtained from Mingle Midges')
    parser.add_argument('--fn', required=True,help='Please enter the path to the file')
    args = parser.parse_args()
    main(fn=args.fn)

