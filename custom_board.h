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
#define MIC_CLK 32
#define MIC_DOUT 31


#endif
