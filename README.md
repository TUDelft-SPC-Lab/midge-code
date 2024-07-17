# "Midge", an SPCL badge

![The MINGLE MIDGE](https://raw.githubusercontent.com/TUDelft-SPC-Lab/spcl_midge_hardware/master/Media/v2.3.jpg)

## Environment Setup:

1. Install the `arm-none-eabi` toolchain (compiler and binutils) for your distro
    * For ubuntu `sudo apt install gcc-arm-none-eabi`
2. Install the opencd debugger [https://openocd.org/](https://openocd.org/)
    * For ubuntu `sudo apt install opencd`
3. Create a folder for housing the SDK in your home folder


```Shell
mkdir ~/nRF5_SDK/15.3.0 -p
```

3. Download nRF5 SDK 15.3.0 from <https://www.nordicsemi.com/Products/Development-software/nrf5-sdk/download>
4. Extract the SDK zip on the folder created in step 2
5. Modify `~/nRF5_SDK/15.3.0/components/toolchain/gcc/Makefile.posix` so
   `GNU_INSTALL_ROOT` points to your `arm-none-eabi` toolchain. In case that the
   distro you are using adds `arm-none-eabi` toolchain installdir to your path,
   you can just set `GNU_INSTALL_ROOT := ` and leave an empty space.
6. modify `~/nRF5_SDK/15.3.0/external/fatfs/src/ffconf.h` to make the `_FS_RPATH`
   define be set as `2`.

### Other requirements:

- You will probably have to use `conda` for setting up a python2 env. In that
  env, you will need to download the `bluepy` module

## How to compile and debug

We are assuming you don't have the Segger J-Link available, but you do have a
spare MCU capable of running a CMSIS-DAP compliant firmware, for example:

- PicoProbe for RP2040 based MCUs like the Pi Pico: <https://github.com/raspberrypi/picoprobe/releases/tag/picoprobe-cmsis-v1.02>
- Seeed DAPLink for Cortex M0 and M4 devices: <https://github.com/Seeed-Studio/Seeed_Arduino_DAPLink/>

### Barebones

1. Build with `make nrf52832_xxaa`
2. Start the openocd server with `make openocd`
3. Start the gdb session and load the binary with `make load_gdb`
4. Start the RTT console to see log messages with `make logs`

### Using Cortex-debug

Just download the [Cortex-Debug](https://marketplace.visualstudio.com/items?itemName=marus25.cortex-debug)
and setup the `.vscode/launch.json`. This should enable the "Run and Debug"
functionality in VSCode (Left menu, green arrow to launch the application).

Example `launch.json` for using Cortex-Debug for flashing and debugging

```JSON
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Cortex Debug",
            "cwd": "${workspaceFolder}",
            "executable": "_build/nrf52832_xxaa.out",
            "request": "launch",
            "type": "cortex-debug",
            "runToEntryPoint": "main",
            "servertype": "openocd",
            "device": "nrf52",
            "configFiles": [
                "interface/cmsis-dap.cfg",
                "target/nrf52.cfg"
            ],
            "openOCDLaunchCommands": ["adapter speed 2000"],
            "interface": "swd",
            "armToolchainPath": "",
            "svdFile": "${workspaceRoot}/nrf52832.svd",
            "preLaunchCommands":["set remotetimeout 60"],
            "rttConfig": {
                "enabled": true,
                "address": "auto",
                "clearSearch": false,
                "decoders": [
                    {
                        "port": 0,
                        "type": "console"
                    }
                ]
            }
        }
    ]
}

```

## Flashing the final binary

//! TODO, but is basically just erasing and reflashing the device via gdb

## Hardware

Hardware design files are in a [separate hardware repo](https://github.com/TUDelft-SPC-Lab/spcl_midge_hardware).

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

On "high" audio is stereo, 20kHz, 16bit per channel PCM.
On "low" it is subsampled by a factor of 32, to 625Hz.

It is only timestamped when the file is created (filename is seconds).

### IMU

Filename is again timestamped, but also each sample (32 bytes):

accelerometer, gyro, magnetometer sample example:
2dd4 a69d 016d 0000 0000 3b40 0000 bc48 2000 3f83 0000 000c 0000 ffce 0000 1064

First 8 bytes are the timestamp:
2dd4 a69d 016d 0000   = 0000016da69d2dd4 = 1570458381780 milliseconds = 07/10/2019 2:26:780

4 bytes float per axis:
0000 3b40   0000 bc48   2000 3f83

padding for data alignment
0000 000c 0000 ffce 0000 1064

Rotation vector:
Timestamp is the same 8 bytes, then 4 floats per quaternion, 4 fewer bytes for padding.

### Scanner

16 byte length
Same 8 byte timestamp.
2 bytes ID
1 int8_t rssi (signed)
1 byte group
4 bytes padding


**the rest should be as you've asked on the requirements, please let me know if something is not clear**
