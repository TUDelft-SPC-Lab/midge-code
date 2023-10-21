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

	def print_help(args):
		print("Available commands: [optional arguments]")
		print("  status [new badge id] [group number] (id + group must be set together)")
		print("  start_microphone")
		print("  stop_microphone")
		print("  start_scan")
		print("  stop_scan")
		print("  start_imu")
		print("  stop_imu")
		print("  identify [led duration seconds | 'off']")
		print("  restart")
		print("  get_free_space")
		print("  help")
		print("All commands use current system time as transmitted time.")
		print("Default arguments used where not specified.")

	def handle_status_request(args):
		if len(args) == 1:
			print(badge.get_status())
		elif len(args) == 2:
			print("Badge ID and Group Number Must Be Set Simultaneously")
		elif len(args) == 3:
			new_id = int(args[1])
			group_number = int(args[2])
			print(badge.get_status(new_id=new_id, new_group_number=group_number))
		else:
			print("Invalid Syntax: status [new badge id] [group number]")

	def handle_start_microphone_request(args):
		print(badge.start_microphone(mode=args))

	def handle_stop_microphone_request():
		badge.stop_microphone()


	def handle_start_scan_request(args):
		print(badge.start_scan(window_ms=args[0], interval_ms=args[1]))

	def handle_stop_scan_request():
		badge.stop_scan()


	def handle_start_imu_request():
		print(badge.start_imu())

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
		print(badge.restart())

	def handle_get_free_space():
		print(badge.get_free_sdc_space())


	command_handlers = {
		"help": print_help,
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
        handle_status_request([1, 65535, 255])
        time.sleep(0.5)
        print("mode: stereo")
        handle_start_microphone_request(0)
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])
        time.sleep(200)
        handle_stop_microphone_request()
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])
        time.sleep(0.5)
        print("mode: mono")
        handle_start_microphone_request(1)
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])
        time.sleep(200)
        handle_stop_microphone_request()
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])
        time.sleep(0.5)
        print("scan test")
        handle_start_scan_request([250, 1000])
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])
        time.sleep(50)
        handle_stop_scan_request()
        handle_status_request([1, 65535, 255])
        time.sleep(0.5)
        print("imu test")
        handle_start_imu_request()
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])        
        time.sleep(50)
        handle_stop_imu_request()
        time.sleep(0.5)
        handle_status_request([1, 65535, 255])
        #time.sleep(0.5)
        

    # Mic Test
    # time.sleep(5)
    #


    # IMU Test
    # time.sleep(5)
    #


    # SCAN Test
    # time.sleep(5)
    #


    # Mic Test
    # time.sleep(5)
    #

if __name__ == "__main__":
	main()
