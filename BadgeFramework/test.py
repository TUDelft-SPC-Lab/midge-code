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

# Enable debug output.
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# Main Loop of Badge Terminal

def main():
	num_args = len(sys.argv) # Get the arguments list
	if num_args != 2:
		print("Please enter badge MAC address")
		return

	device_addr = sys.argv[1]
	print("Connecting to badge", device_addr)
	connection = BLEBadgeConnection.get_connection_to_badge(device_addr)

	if not connection:
		print("Could not find nearby OpenBadge. :( Please try again!")
		return

	connection.connect()
	badge = OpenBadge(connection)

	print("Connected!")


	def handle_status_request(args):
		if len(args) == 1:
			badge.get_status()
		elif len(args) == 2:
			print("Badge ID and Group Number Must Be Set Simultaneously")
		elif len(args) == 3:
			new_id = int(args[1])
			group_number = int(args[2])
			badge.get_status(new_id=new_id, new_group_number=group_number)
		else:
			print("Invalid Syntax: status [new badge id] [group number]")

	def handle_start_microphone_request(args):
		badge.start_microphone(mode=args)

	def handle_stop_microphone_request():
		badge.stop_microphone()


	def handle_start_scan_request(args):
		badge.start_scan(window_ms=args[0], interval_ms=args[1])

	def handle_stop_scan_request():
		badge.stop_scan()


	def handle_start_imu_request():
		badge.start_imu()

	def handle_stop_imu_request():
		badge.stop_imu()


	def handle_identify_request(args):
		if (len(args) == 1 or len(args) == 0):
			badge.identify()
		elif len(args) == 2:
			if args[1] == "off":
				badge.identify(duration_seconds=0)
			else:
				badge.identify(duration_seconds=int(args[1]))
		else:
			print("Invalid Syntax: identify [led duration seconds | 'off']")
			return

	def handle_restart_request():
		badge.restart()

	def handle_get_free_space():
		badge.get_free_sdc_space()


	command_handlers = {
		"status": handle_status_request,
		"start_microphone": handle_start_microphone_request,
		"stop_microphone": handle_stop_microphone_request,
		"start_scan": handle_start_scan_request,
		"stop_scan": handle_stop_scan_request,
		"start_imu": handle_start_imu_request,
		"stop_imu": handle_stop_imu_request,
		"identify": handle_identify_request,
		"restart": handle_restart_request,
		"get_free_space": handle_get_free_space,
	}

	for reps in 1, 2:
		time.sleep(0.5)
        print("microphone test")
        time.sleep(0.5)
        print("mode: stereo")

        if (~badge.start_microphone(0).mode):
            mic_mode_stereo = True
        else:
            mic_mode_stereo = False

        time.sleep(20)

        if (badge.get_status().microphone_status & mic_mode_stereo):
            mic_enabled_stereo = True
        else:
            mic_enabled_stereo = False

        handle_stop_microphone_request()
        time.sleep(0.5)

        if (~badge.get_status().microphone_status & mic_enabled_stereo):
            print("Mic Stereo: PASS")
        else:
            print("Mic Stereo: FAIL")		
        print("mode: mono")

        if (badge.start_microphone(1).mode):
            mic_mode_mono = True
        else:
            mic_mode_mono = False

        time.sleep(20)

        if (badge.get_status().microphone_status & mic_mode_mono):
            mic_enabled_mono = True
        else:
            mic_enabled_mono = False

        handle_stop_microphone_request()
        time.sleep(0.5)

        if (~badge.get_status().microphone_status & mic_enabled_stereo):
            print("Mic Mono: PASS")
        else:
            print("Mic Mono: FAIL")

        print("scan test")

        badge.start_scan(window_ms = 250, interval_ms = 1000)
	
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])
        time.sleep(20)
        if (badge.get_status().scan_status):
            print("Start Scan: PASS")
        else:
            print("Start Scan: FAIL")
        handle_stop_scan_request()
        handle_status_request([1, 65535, 255])
        time.sleep(0.5)
        if (~badge.get_status().scan_status):
            print("Stop Scan: PASS")
        else:
            print("Stop Scan: FAIL")		
        print("imu test")
        handle_start_imu_request()
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])        
        time.sleep(20)
        if (badge.get_status().imu_status):
            print("Start IMU: PASS")
        else:
            print("Start IMU: FAIL")	
        handle_stop_imu_request()
        time.sleep(0.5)
        if (~badge.get_status().imu_status):
            print("Stop IMU: PASS")
        else:
            print("Stop IMU: FAIL")	

if __name__ == "__main__":
	main()
