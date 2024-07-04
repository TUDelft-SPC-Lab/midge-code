set remotetimeout 60
target extended-remote :3333
monitor rtt setup 0x200041ac 1280 "SEGGER RTT"
set print asm-demangle on
load 
break main.c:38
continue
monitor rtt start 
monitor rtt server start 8000 0

