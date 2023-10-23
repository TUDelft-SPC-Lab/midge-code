#ifndef CUSTOM_BOARD_SPCL_H
#define CUSTOM_BOARD_SPCL_H

/**
 * LED_IND PO.03 pin 19
 * SCL     PO.02 pin 15
 * SDA     PO.00 pin 13
 * INT1    PO.30 pin 11
 * CD      PO.09 pin 25
 * SW      PO.11 pin 27
 * CS      PO.15 pin 25
 * MOSI    PO.16 pin 34
 * CLK     PO.17 pin 35
 * MISO    PO.18 pin 38
 * BATSEN  PO.05 pin 21
 * MICDOUT PO.13 pin 31
 * MICCLK  PO.14 pin 32
 * SW2OFF  PO.25 pin 6
 * SW2LOW  PO.26 pin 7
 * SW2HIGH PO.27 pin 8
 */

// I2C pins
#define TWI_SCL 02
#define TWI_SDA 00
#define INT1_PIN 30

// SPI pins
#define SDC_CS_PIN 15
#define SDC_MOSI_PIN 16
#define SDC_SCK_PIN 17
#define SDC_MISO_PIN 18

// microphone pins
#define MIC_CLK 14
#define MIC_DOUT 13

// LED
#define LED 03
#define LED_ON 1
#define LED_OFF 0

// AUDIO
#define AUDIO_SWITCH_OFF 25
#define AUDIO_SWITCH_LOW 26
#define AUDIO_SWITCH_HIGH 27

#endif
