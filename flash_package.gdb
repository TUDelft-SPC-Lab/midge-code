target extended-remote :3333
monitor reset halt
monitor program _build/spcl.hex verify
monitor reset
quit

