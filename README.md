# "Midge", an SPCL badge

![The MINGLE MIDGE](https://raw.githubusercontent.com/TUDelft-SPC-Lab/spcl_midge_hardware/master/Media/v2.3.jpg)

The Midge is a small, low-power wearable device designed to record audio, orientation and proximity data.
It features a Nordic nRF52832 microcontroller, Bluetooth connectivity, dual microphones, an IMU (Inertial Measurement Unit), and a microSD card slot for local data storage.

This repository contains the firmware for the Midge.
It also contains the software that is used for monitoring and controlling the midge, recording and processing the data.


## Sensors

The **IMU** combines an accelerometer, gyroscope, and magnetometer to accurately capture the midge orientation.
The samples are stored in a binary file, with each sample containing a timestamp and the sensor data.
The samples are recorded at a best effort of 56 Hz, meaning that the actual sample rate varies slightly depending on the device's processing load.

**Proximity** is measured using a Bluetooth scanner capable of detecting nearby devices.
Each midge send Bluetooth broadcasts packages at 1 Hz.
The scanner records the ID, RSSI (Received Signal Strength Indicator), and group for each detected package.
These samples are also stored in a binary file.

**Audio** can be recorded in two modes: low-frequency (1.25 kHz) and high-frequency (20 kHz).
The low-frequency mode is optimized for privacy-preserving applications; it does not capture intelligible speech but can detect the presence of vocal activity.
Two files are created per session, a binary file containing the raw audio data, and another binary file containing the timestamps for each audio sample. 

# Data recording workflow

## Requirements
1. Create a python2 virtual environment and activate it.
2. Install the dependencies `pip install bluepy pandas numpy matplotlib seaborn tqdm`.
3. Install [Tkinter](https://wiki.python.org/moin/TkInter).

Note that the bluepy dependency only works on linux.

You can use the nix file to create a development environment with all the dependencies installed.

With conda you can install the dependencies with:
```bash
conda create -n midge python=2.7
conda activate midge
pip install bluepy pandas numpy matplotlib seaborn tqdm
conda install -c conda-forge tk
```

## Recording data
1. Turn the midges on
2. Get their MAC address with either of these options
    * With the `scan_all.py` script
    * Running the following command in a terminal
        ```bash
        (echo -e 'power on\nscan on\n'; sleep 5; echo 'scan off') | \
        bluetoothctl > /dev/null 2>&1 && bluetoothctl devices | grep HDBDG
        ```
4. Start recording 
    * Use `badge_gui.py` if you have 5 or fewer midges.
    This provides a nice GUI interface to control them.
    * Use the `hub.py` if you have 6 or more midges.
    This provides a command line script that can control multiple midges sequentially.
5. Stop recording
6. Copy the data from the SDCards into a computer, there are two options:
    * Take the card manually out of the midge, plug it in the computer and copy the files.
    * Use the `download_all` command in the `terminal.py` script to download the data over Bluetooth.
7. Run processing data scripts to transform the raw data into common file formats: `imu_parser.py` and `audio_parser.py`
    * The audio files can also be decoded with Audacity (File -> Import -> Raw Data) using the same parameters that are used in `audio_parser.py`. 


# Development

Hardware design files can be found in the [hardware repo](https://github.com/TUDelft-SPC-Lab/spcl_midge_hardware).

For firmware development check the [firmware page](FIRMWARE.md).

The data structure for the sensor raw data in the binary files is defined in the [raw data format page](RAW_DATA_FORMAT.md).

In the same page, the [bluetooth advertisement packet structure](RAW_DATA_FORMAT.md#bluetooth-advertisement-packet-structure) is also defined.