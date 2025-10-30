## Binary files data format

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
The data part represents a quaternion containing 4 floats, in scalar-last format (x, y, z, w).

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

## Bluetooth advertisement packet structure

The advertisement packet has a field called "manufacturer specific data", with type 0xFF.

It starts at the 12th byte. Its length is 11 bytes:

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
Battery is in percentage, and the status flags are:
* bit 0: clock sync
* bit 1: microphone
* bit 2: scanner
* bit 3: imu

0 is not active, 1 active.