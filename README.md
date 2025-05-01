# "Midge", an SPCL badge

![The MINGLE MIDGE](https://raw.githubusercontent.com/TUDelft-SPC-Lab/spcl_midge_hardware/master/Media/v2.3.jpg)

## Environment Setup:

1. Install the `arm-none-eabi` toolchain (compiler and binutils) for your distro <https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads>
    * To avoid issues it is recommended to have matching `gcc` and `gdb` versions from the toolchain
    * The `gdb-multiarch` package in ubuntu is know to cause debug errors when used with the `arm-none-eabi`'s `gcc`.
    * Version 13.3 is known to work well
2. Install the openocd debugger 
    * For ubuntu `sudo apt install openocd`
    * For a different OS: <https://openocd.org/>
3. Install the dependencies for visualising the debug logs:
    * For ubuntu `sudo apt install socat picocom`
    * For a different OS: TODO
3. Install the nRF5 SDK
    * Download the nRF5 SDK version 15.3.0 from <https://www.nordicsemi.com/Products/Development-software/nrf5-sdk/download>
    * Create a folder for housing the SDK in your home folder
        ```Shell
        mkdir ~/nRF5_SDK_15.3.0 -p
        ```
    * Extract the SDK zip in the folder created in the previous step
    * Modify `~/nRF5_SDK_15.3.0/components/toolchain/gcc/Makefile.posix` so `GNU_INSTALL_ROOT` points to your `arm-none-eabi` toolchain.
      If the binary is already in your `PATH`, so just set `GNU_INSTALL_ROOT :=`.
      For example `GNU_INSTALL_ROOT ?= /home/user/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi/bin/`
    * Modify `~/nRF5_SDK_15.3.0/external/fatfs/src/ffconf.h` to make the `_FS_RPATH` macro be defined as `2`.
    * For ubuntu if the sdk complains about missing `libncursesw.so.5` install it with `sudo apt install libncursesw5`.  

### Other requirements:

- You will probably have to use `conda` for setting up a python2 env. In that
  env, you will need to download the `bluepy` module

### Using Nix:
This project includes a `flake.nix` file that automatically sets up the development environment with all required dependencies.
1. Install Nix package manager by following instructions at nixos.org
2. Enable flakes by either:
    * Adding `experimental-features = nix-command flakes` to your `~./config/nix/nix.conf`
    * Or using the `-E` flash with each nix command
3. Enter the development shell:
    ```shell
    nix develop
    ```
    This will setup an environment with:
        * ARM GCC toolchain (gcc-arm-embedded-13)
        * socat and picocom for debug logs
        * Python with required packages
        * C development tools
4. Alternatively, you can use direnv to automatically enter the environment:
    * Install direnv from direnv.net
    * Run `direnv allow` in the project directory

## Board options

There are several MCU boards that can be used for compiling and debuging the midge fimware.
The main requisite is that they can run CMSIS-DAP compliant firmware.
The Segger J-Link is known to provide the fastest data transfer rates, while the the Seeed XIAO SAMD21 board is more affordable and easier to acquire.

### Seeed XIAO SAMD21 board
We use the [Seeed XIAO SAMD21 board](https://wiki.seeedstudio.com/Seeeduino-XIAO/) with the [Seeed DAPLink](https://github.com/Seeed-Studio/Seeed_Arduino_DAPLink) for Cortex M0 and M4 devices.

Additionally you will need the following components:
* A pogo pin probe clip https://www.adafruit.com/product/5434
  * For a permanent solution, soldering the pins via a box header is also an option https://www.adafruit.com/product/752 
* Female to female jumper wires https://www.adafruit.com/product/1951 (this examples comes with 20, only 3 are needed)

Flash the DAPLink firmware in the SAMD21 board (only needs to be done once):
1. Connect the board to the computer via usb
2. Put the board in bootloader mode as described [here](https://wiki.seeedstudio.com/Seeeduino-XIAO/#enter-bootloader-mode), it should show up as usb stick in the computer
3. Copy over the uf2 file from [here](http://files.seeedstudio.com/wiki/Seeeduino-XIAO/res/simple_daplink_xiao.uf2)
4. Disconnect and reconnect the usb cable
5. Connect the midge to the board and the board to the computer as described in [here](#Hardware-connection-to-the-board)
6. The flashing was performed successfully if the LEDs in the board turned blue and stoped flashing

### PicoProbe for RP2040 
The PicoProbe for RP2040 based MCUs like the [Pi Pico](https://github.com/raspberrypi/picoprobe/releases/tag/picoprobe-cmsis-v1.02) should also work.
   * TODO: add instructions for this board 

### Segger J-Link

1. Get a J-link debug probe from here:  https://www.segger.com/products/debug-probes/j-link/
The EDU version is available for educational instituions. 
2. Download and install the J Link SDK from [here](https://www.segger.com/products/debug-probes/j-link/tools/j-link-sdk/).
3. Make sure the midge badge is powered on, and connect the J-link to the SWD programming port on the midge badge. 
4. Open your terminal (or command prompt) and enter the following command to start J-Link Commander and connect to the nRF52832 using SWD at a speed of 4 MHz:
   ```
   JLinkExe -device nRF52832_xxAA -if SWD -speed 4000
   ```
5. Flash the binary file:
   ```
   loadfile <firmware.hex>
   ```

### Hardware connection to the board

Openocd is known to crash with `Error connecting DP: cannot read IDR` when debugging the midge while plugged in to power.
To ensure a smooth debugging process follow these steps when connecting the midge to the computer.

1. Make sure the battery charged
2. Connect the board to the pogo pin and the pogo pin to the midge
   * The pin connections to the midge are described [here](https://github.com/TUDelft-SPC-Lab/spcl_midge_hardware/blob/master/PCB/Explainer.pdf)
   * The pin connections to the boards are as follows: 
      * Seeed XIAO SAMD21 board, described [here](https://wiki.seeedstudio.com/Seeeduino-XIAO/#hardware-overview) and [here](https://github.com/Seeed-Studio/Seeed_Arduino_DAPLink/blob/master/src/DAP_config.h#L179-L188)
      * TODO: add pin connections for the other boards
   * Note that the pogo pin switches around the A and B side of the pins
   * Do not connect the 3V pin, only the SWDIO, SWCLK and GND pins should be attached
3. Disconnect the charging cable of the midge before debugging
4. After having the connections ready, connect the debug probe to the computer 
5. Switch ON the battery

## Compile and debug

There are two options for compiling and debugging the code.
A barebones gdb server that can be executed via Makefile rules or using the VScode IDE with the Cortex-debug plugin.

### Using Makefile rules

1. Build with `make nrf52832_xxaa_debug`
2. Start the openocd server with `make openocd`
3. Start the gdb session and load the binary with `make load_gdb`
4. Start the RTT console to see log messages with `make logs`

### Using VSCode with Cortex-debug

Just download the [Cortex-Debug](https://marketplace.visualstudio.com/items?itemName=marus25.cortex-debug) and setup the `.vscode/launch.json`.
This should enable the "Run and Debug" functionality in VSCode (Left menu, green arrow to launch the application).
In the C++ extension `ms-vscode.cpptools` set the configuration to `arm-none-eabi` to get include paths for the SDK recognised by intellisense.

Example `launch.json` for using Cortex-Debug for flashing and debugging

```JSON
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Cortex Debug",
            "cwd": "${workspaceFolder}",
            "executable": "_build/nrf52832_xxaa_debug.out",
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

### About the BLE stack AKA softdevice 

A softdevice is basically the stack used for controlling the different radios 
in a nRF chip. It's a binary that must be flashed before other firmware. It can 
be downloaded as a standalone binary, altough if you already had the nRF5 SDK 
downloaded, it's probably already coupled with it. You should be able to find it
at `$(SDK_ROOT)/components/softdevice/s132/hex/s132_nrf52_6.1.1_softdevice.hex`.
The standalone files can be downloaded from
<https://www.nordicsemi.com/Products/Development-software/S132/Download>

### DAPLink

1. Flash the softdevice (only required once): `make daplink_flash_softdevice`
  - This by itself will call the `daplink_erase_flash` target which erases 
    contents of code memory and config registers
2. Build with `make nrf52832_xxaa_<release|debug>`
3. Flash the binary with `make daplink_flash_<release|debug>`

> Calling the `daplink_erase_flash` target is not a requirement to update 
  firmware after the softdevice has been flashed

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

Audio can be recorded in either stereo o mono. The files saved to the SD cards
are raw audio files, 16 bit signed PCM. Name of the file indicates the 
parameters used for recording with the general pattern looking like 
`[0|1]MIC[HI|LO][audio recording #]`:

- Name start:
    - `0`: Stereo
    - `1`: Mono

- Text after `MIC`:
    - `HI`: Audio recorded at base platform sample rate aka ("HIGH") frequency (~16KHz)
    - `LO`: Audio recording where data is decimated to obtain a low-frequency only recording 

> The base platform sample rate is obtained via the calculation: 
`(PDM_CLK_SOURCE/PDM_CLK_DIVIDER)/PDM_TO_PCM_DIV`. In the current HW, 
`PDM_CLK_SOURCE` is 32MHz, the `PDM_CLK_DIVIDER` param depends on the microphone
configuration in firmware, and the `PDM_TO_PCM_DIV` value is 64. The values of
interest can be found in the nRF5 SDK documentation for the nRF52832 for the 
PDM peripheral. 

> Decimation factor for low frequency audio is defined in firmware in the 
`microphone` folder.

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


# Data recording workflow

1. Turn the midges on
2. Get their MAC address with the `scan_all.py` script
3. Start recording via `hub_V1.py` or the `badge_gui.py` scripts using the previous MAC addresses
4. Stop recording
5. Copy the data from the SDCards into a computer (for this step, take the card manually out of the midge and
   plug it in the computer) 
6. Run processing data scripts to transform the raw data into common file formats: `imu_parser_V0.py` and `audio_parser_V0.py`


