from __future__ import division, absolute_import, print_function
import logging
import sys
import threading
import time

from badge import *
from ble_badge_connection import *
from bluepy import *
from bluepy import btle
from bluepy.btle import UUID, Peripheral, DefaultDelegate, AssignedNumbers ,Scanner
from bluepy.btle import BTLEException


def main():
	device_addr = sys.argv[1]
	print("#####################################")
	print("# Connecting to ", device_addr, " # ")
	connection = BLEBadgeConnection.get_connection_to_badge(device_addr)

	if not connection:
		print("# Could not find badge            #")
		return

	connection.connect()
	badge = OpenBadge(connection)

	print("# connetced                         #")

	for reps in 1, 2:


		time.sleep(0.5)
        print("#####################################")
        print("# Midge test                        #")
        print("# sensor: mic, stereo mode          #")
        print("#-----------------------------------#")
        if (~badge.start_microphone(0).mode):
            mic_mode_stereo = True
            print("# mic mode:         PASS            #")
        else:
			mic_mode_stereo = False
			print("# mic mode:         FAIL             #")

        time.sleep(5)

        if (badge.get_status().microphone_status & mic_mode_stereo):
			print("# mic enabled:      PASS            #")
			mic_enabled_stereo = True
        else:
            mic_enabled_stereo = False
            print("# mic enabled:      FAIL            #")

        badge.stop_microphone()
	
        time.sleep(0.5)

        if (~badge.get_status().microphone_status & mic_enabled_stereo):
            print("# overall ressult:  PASS            #")
        else:
            print("# overall ressult:  FAIL            #")


        print("#####################################")
        print("# sensor: mic, mono mode            #")
        print("#-----------------------------------#")

        if (~badge.start_microphone(1).mode):
			mic_mode_mono = True
			print("# mic mode:         PASS            #")
        else:
			mic_mode_mono = False
			print("# mic mode:         FAIL             #")

        time.sleep(5)

        if (badge.get_status().microphone_status & mic_mode_mono):
			mic_enabled_mono = True
			print("# mic enabled:      PASS            #")
        else:
			mic_enabled_mono = False
			print("# mic enabled:      FAIL            #")

        badge.stop_microphone()
	
        time.sleep(0.5)

        if (~badge.get_status().microphone_status & mic_enabled_stereo):
            print("# overall ressult:  PASS            #")
        else:
            print("# overall ressult:  FAIL            #")

        print("#####################################")
        print("# sensor: scan                      #")
        print("#-----------------------------------#")

        badge.start_scan(window_ms = 250, interval_ms = 1000)
	
        time.sleep(5)
	
        if (badge.get_status().scan_status):
            print("# scan enabled:     PASS            #")
        else:
            print("# scan enabled:     FAIL            #")
	    
        badge.stop_scan()

        time.sleep(0.5)
        if (~badge.get_status().scan_status):
			print("# scan disabled:    PASS            #")
			print("# overall ressult:  PASS            #")
        else:
			print("# scan disabled:    FAIL            #")
			print("# overall ressult:  FAIL            #")	
	    
        print("#####################################")
        print("# sensor: imu                       #")
        print("#-----------------------------------#")
	
        badge.start_imu()
     
        time.sleep(5)
	
        if (badge.get_status().imu_status):
			print("# imu enabled:      PASS            #")
			print("# overall ressult:  PASS            #")
        else:
			print("# imu enabled:      FAIL            #")
			print("# overall ressult:  FAIL            #")	
        badge.stop_imu()
        time.sleep(0.5)
        if (~badge.get_status().imu_status):
			print("# imu disbled:      PASS            #")
			print("# overall ressult:  PASS            #")
			print("#####################################")
        else:
			print("# imu enabled:      FAIL            #")
			print("# overall ressult:  FAIL            #")
			print("#####################################")

			
	badge.sdc_errase_all		

if __name__ == "__main__":
	main()