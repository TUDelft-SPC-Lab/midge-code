define run_with_rtt
    run 
    next
    next
    monitor rtt setup $SEGGER_RTT_ADDRESS 1280 "SEGGER RTT"
    monitor rtt start 
end 

set remotetimeout 60
target extended-remote :3333
set print asm-demangle on
monitor rtt server start 8000 0
load 
break main
run_with_rtt
