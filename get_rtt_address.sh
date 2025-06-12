#!/bin/bash

set -e # Exit if any command fails

NM_OUTPUT=$(arm-none-eabi-nm ./_build/nrf52832_xxaa_debug.out)
SEGGER_RTT_LINE=$(echo "$NM_OUTPUT" | grep _SEGGER_RTT)
export SEGGER_RTT_ADDRESS=0x$(echo "$SEGGER_RTT_LINE" | awk '{print $1}')

if [[ -n "$SEGGER_RTT_ADDRESS" ]]; then
    echo "$SEGGER_RTT_ADDRESS"
else
    echo "Could not find _SEGGER_RTT address." >&2
    exit 1
fi

# The .gdb env does not support variable expansion directly, so we use envsubst to replace the variable in the file.
envsubst < debug.gdb > _build/debug.gdb
