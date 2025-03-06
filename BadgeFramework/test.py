from __future__ import division, absolute_import, print_function
import logging
import sys
import threading
import time
from datetime import datetime
import utils
from badge import OpenBadge
from bleak import BleakClient, BLEDevice, BleakGATTCharacteristic, BleakScanner
import asyncio
# from ble_badge_connection import *


async def mic_test(badge, mode):
    if (mode==0):
        start_stereo = await badge.start_microphone(t=None,mode=0) # start mic in stereo mode
        print(" sensor: mic, stereo mode            ")        
        # check if mic was started in stereo mode
        if (start_stereo.mode==0):
            print(" mic mode:         PASS            ")
            if (start_stereo.pdm_freq == 1000 or start_stereo.pdm_freq == 1032 or start_stereo.pdm_freq == 1067):
                print(" mic freq:         PASS            ")
            else:
                print(" mic freq:         FAIL            ")

            if (start_stereo.gain_l != 0 and start_stereo.gain_r != 0):
                print(" mic gain:         PASS            ")
            else:
                print(" mic gain:         FAIL            ")               
        else:
            print(" mic mode:         FAIL             ")

        time.sleep(10) # reecording time

        mic = await badge.get_status()
        # check if mic was enabled 
        if (mic.microphone_status):
            print(" mic enabled:      PASS            ")
        else:
            print(" mic enabled:      FAIL            ")

        await badge.stop_microphone() # stop recording

        time.sleep(0.5)

        mic = await badge.get_status()
        # check if mic was disabled with success
        if (~mic.microphone_status):
            print(" mic disabled:     PASS            ")
        else:
            print(" mic disabled:     PASS            ")
    else:
        print("###################################")
        print(" sensor: mic, mono mode            ")
        #print("-----------------------------------")

        start_mono = await badge.start_microphone(t=None,mode=1)

        if (start_mono.mode==1):
            print(" mic mode:         PASS            ")
            if (start_mono.pdm_freq == 1000 or start_mono.pdm_freq == 1032 or start_mono.pdm_freq == 1067):
                print(" mic freq:         PASS            ")
            else:
                print(" mic freq:         FAIL            ")

            if (start_mono.gain_l != 0 and start_mono.gain_r != 0):
                print(" mic gain:         PASS            ")
            else:
                print(" mic gain:         FAIL            ")                
            
        else:
            print(" mic mode:         FAIL            ")

        time.sleep(10) # reecording time

        mic = await badge.get_status()
        # check if mic was enabled 
        if (mic.microphone_status):
            print(" mic enabled:      PASS            ")
        else:
            print(" mic enabled:      FAIL            ")

        await badge.stop_microphone() # stop recording

        time.sleep(0.5)

        mic = await badge.get_status()
        # check if mic was disabled with success
        if (~mic.microphone_status):
            print(" mic disabled:     PASS            ")
        else:
            print(" mic disabled:     PASS            ")

async def imu_test(badge):
    print("###################################")
    print(" sensor: imu                       ")
    #print("#-----------------------------------#")

    imu_start = await badge.start_imu() # start imu
    time.sleep(0.1) # safety wait 
    #check if imu self test was done
    if (imu_start.self_test_done):
        print(" imu self test:    PASS            ")
    else:
        print(" imu self test:    FAIL            ")

    imu = await badge.get_status() # get imu status
    time.sleep(0.1) # safety wait 
    imu_data = await badge.get_imu_data() # get imu data

    #print(imu_data)
    
    # check if imu sensors are sending data 
    if (imu.imu_status):
        print(" imu enabled:      PASS            ")
        if (~(imu_data.acc_x == 0 and imu_data.acc_y  == 0 and imu_data.acc_z  == 0)):
            print(" imu acc:          PASS            ")
        else:
            print(" imu acc:          FAIL            ")
        if (~(imu_data.mag_x == 0 and imu_data.mag_y  == 0 and imu_data.mag_z  == 0)):
            print(" imu mag:          PASS            ")
        else:
            print(" imu mag:          FAIL            ")
        if (~(imu_data.gyr_x == 0 and imu_data.gyr_y  == 0 and imu_data.gyr_z  == 0)):
            print(" imu gyr:          PASS            ")
        else:
            print(" imu gyr:          FAIL            ")
        if (~(imu_data.rot_x == 0 and imu_data.rot_y  == 0 and imu_data.rot_z  == 0)):
            print(" imu rot:          PASS            ")
        else:
            print(" imu rot:          FAIL            ")

    else:
        print(" imu enabled:      FAIL            ")

    
    time.sleep(10) # imu enabled time
    await badge.stop_imu()
    time.sleep(0.5) # safety wait

    imu = await badge.get_status()

    if (~imu.imu_status):
        print(" imu disabled:     PASS            ")
    else:
        print(" imu disabled:     FAIL            ")


async def scan_test(badge):
    print("###################################")
    print(" sensor: scan                      ")
    #print("#-----------------------------------#")

    await badge.start_scan(window_ms = 250, interval_ms = 1000) ## start scan with default parameters
    time.sleep(10) # scan enabled time  

    scan = await badge.get_status()
    # check if scan was enabled succesfully
    if (scan.scan_status):
        print(" scan enabled:     PASS            ")
    else:
        print(" scan enabled:     FAIL            ")
    # check if scan was sending data (must have another badge near to pass)
    if (scan.scan_data != 0):
        print(" scan data:        PASS            ")            
    else:
        print(" scan data:        FAIL            ")
    
    await badge.stop_scan() # stop scan

    time.sleep(0.5) # safety wait

    scan = await badge.get_status() # get scan status
    # check if scan was disabled succesfully
    if (~scan.scan_status):
        print(" scan disabled:    PASS            ")		
    else:
        print(" scan disabled:    FAIL            ")


async def errase_mem(badge):
    errased = await badge.sdc_errase_all() # clean sd memory

    if (errased.done_errase):
        print(" memory cleaned:   PASS            ")
        print("###################################")
    else:
        print(" memory cleaned:   FAIL            ")
        print("###################################")

    # def connect(self):
    #     connection = BLEBadgeConnection.get_connection_to_badge(self.address)
    #     connection.connect()
    #     badge = OpenBadge(self.connection)
    #     print("Connected!")
    #     return badge


async def main():
    # device_addr = sys.argv[1]

    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)

    # Filter out the devices that are not the midge
    devices = [d for d in devices.values() if utils.is_spcl_midge(d[0])]

    if devices:
        ble_device, adv_data = devices[0]
    else:
        print("No devices found")
        return

    try:
        async with OpenBadge(ble_device) as open_badge:
            print(" connetced                         ")
            print("###################################")
            print(" Midge test                        ")
            try:
                await mic_test(open_badge, 0)
            except:
                print("mic error")

            try:
                await mic_test(open_badge, 1)
            except:
                print("mic error")

            try:
                await scan_test(open_badge)
            except:
                print("scan error")

            try:
                await imu_test(open_badge)
            except:
                print("imu error")

            try:
                await errase_mem(open_badge)
            except:
                print("errase memory error")

    except TimeoutError:
        print("failed to connect to device")


async def communicate_with_device(ble_device):
    try:
        async with OpenBadge(ble_device) as open_badge:
            # async with OpenBadge(int(device_id), ble_device.address) as open_badge:
            out = await open_badge.get_status()
            # start = await open_badge.start_microphone()
            print(out)
    except TimeoutError:
        print("failed to connect to device")

async def test_conn():
    logger = utils.get_logger('bleak_logger')
    # Find all devices
    # using both BLEdevice and advertisement data here since it has more information. Also mutes the warning.
    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)

    # Filter out the devices that are not the midge
    devices = [d for d in devices.values() if utils.is_spcl_midge(d[0])]

    # Print Id to see if it matches with any devices in the csv file.
    for ble_device, adv_data in devices:
        device_id = utils.get_device_id(ble_device)
        print(f"RSSI: {adv_data.rssi}, Id: {device_id}, Address: {ble_device.address}")

    tasks = [communicate_with_device(ble_device) for ble_device, adv_data in devices]
    await asyncio.gather(*tasks)

    print(f'after connection: {datetime.now().timestamp()}')

if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(test_conn())
