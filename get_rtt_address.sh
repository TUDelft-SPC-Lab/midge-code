#!/bin/bash

set -e # Exit if any command fails

NM_OUTPUT=$(arm-none-eabi-nm ./_build/nrf52832_xxaa_debug.out)
SEGGER_RTT_LINE=$(echo "$NM_OUTPUT" | grep _SEGGER_RTT)
SEGGER_RTT_ADDRESS=0x$(echo "$SEGGER_RTT_LINE" | awk '{print $1}')

if [[ -n "$SEGGER_RTT_ADDRESS" ]]; then
    echo "$SEGGER_RTT_ADDRESS"
else
    echo "Could not find _SEGGER_RTT address." >&2
    exit 1
fi
   