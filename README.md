# "Midge", an SPCL badge

![The MINGLE MIDGE](https://raw.githubusercontent.com/TUDelft-SPC-Lab/spcl_midge_hardware/master/Media/v2.3.jpg)

The Midge is a small, low-power wearable device designed to record audio, orientation and proximity data.
It features a Nordic nRF52832 microcontroller, Bluetooth connectivity, dual microphones, an IMU (Inertial Measurement Unit), and a microSD card slot for local data storage.

This repository contains the firmware for the Midge.
It also contains the software that is used for monitoring and controlling the midge, recording and processing the data.

The **IMU** combines an accelerometer, gyroscope, and magnetometer to accurately capture and process orientation data.
The samples are stored in a binary file, with each sample containing a timestamp and the sensor data.
The samples are recorded at a best effort of 56 Hz, meaning that the actual sample rate varies slightly depending on the device's processing load.

**Proximity** is measured using a Bluetooth scanner capable of detecting nearby devices.
Each midge send Bluetooth broadcasts packages at 1 Hz.
The scanner records the ID, RSSI (Received Signal Strength Indicator), and group for each detected package.
These samples are also stored in a binary file.

**Audio** can be recorded in two modes: low-frequency (1.25 kHz) and high-frequency (20 kHz).
The low-frequency mode is optimized for privacy-preserving applications; it does not capture intelligible speech but can detect the presence of vocal activity.
Two files are created per session, a binary file containing the raw audio data, and another binary file containing the timestamps for each audio sample. 

## Hardware

Hardware design files can be found in the [hardware repo](https://github.com/TUDelft-SPC-Lab/spcl_midge_hardware).

## Firmware development

For firmware development check the [firmware page](FIRMWARE.md).

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

## Advertisment Packet structure

The advertisment packet has a field called "manufacturer specific data", with type 0xFF. It should start at the 12th byte. Its length is 11 bytes:

```C
typedef struct
{
    uint8_t battery;
    uint8_t status_flags;
    uint16_t ID;
    uint8_t group;
    uint8_t MAC[6];
} custom_advdata_t;
```

MAC is set during init, ID and group with the status command.
Battery is in percentage, and the status flags are :
bit 0: clock sync
bit 1: microphone
bit 2: scanner
bit 3: imu

0 is not active, 1 active.

## Data format

### Audio

Audio can be recorded in either stereo o mono.
The files saved to the SD cards are raw audio files, 16 bit signed PCM.
The name of the file indicates the parameters used for recording with the general pattern looking like 
`[0|1]MIC[HI|LO][audio recording #]`:

- Name start:
    - `0`: Stereo
    - `1`: Mono

- Text after `MIC`:
    - `HI`: Audio recorded at base platform sample rate aka ("HIGH") frequency (20 kHz)
    - `LO`: Audio recording where data is decimated to obtain a low-frequency only recording 

> The base platform sample rate is obtained via the calculation: 
`(PDM_CLK_SOURCE/PDM_CLK_DIVIDER)/PDM_TO_PCM_DIV`. In the current HW, 
`PDM_CLK_SOURCE` is 32 MHz, the `PDM_CLK_DIVIDER` param depends on the microphone
configuration in firmware, and the `PDM_TO_PCM_DIV` value is 64. The values of
interest can be found in the nRF5 SDK documentation for the nRF52832 for the 
PDM peripheral.

> Decimation factor for low frequency audio is defined in firmware in the 
`microphone` folder.

### IMU

The IMU data is stored in a binary file.
The sensors record samples at a best effort of 56 Hz, i.e. often there are fewer samples.
Each sample is 24 bytes long.
The first 8 bytes contain the timestamp, the next 12 the data and last 4 bytes are padding.

For example:
```
 2dd4 a69d 016d 0000 0000 3b40 0000 bc48 2000 3f83 0000 0000
|---- Timestamp ----|----------  Data  -----------|-- Padding --|
```

Timestamp
```
2dd4 a69d 016d 0000   = 0000016da69d2dd4 = 1570458381780 milliseconds = 07/10/2019 2:26:780
```

The data is 4 bytes float per axis:
```
 0000 3b40   0000 bc48   2000 3f83
|---- X ---|---- Y ----|--- Z ----|
```

```
 0000 3b40   = 1.0
 0000 bc48   = -1.0
 2000 3f83   = 0.5
```
padding for data alignment, these bytes are ignored
```
0000 0000
```

The samples for the rotation are different: 8 bytes for the timestamp and 16 bytes of data.
The data part represents a quaternion containing 4 floats. 

### Scanner

The scanner data is also stored in a binary file.
The sensor records samples at 1 Hz, where each scan window lasts 0.25 seconds.
Each sample is 16 bytes long.
The first 8 bytes are the timestamp, the next 2 bytes are the ID, the next byte is the RSSI, and the next byte is the group and the last 4 are for padding.

16 bytes of data
```
 2dd4 a69d 016d 0000 0000 3b40 0000 bc 48
|---- Timestamp ----|-----  Data  ----|- Padding -|
```
