from __future__ import division, absolute_import, print_function
import logging
import sys
import threading
import time
from datetime import datetime
import utils
from badge import OpenBadge
from bleak import BleakScanner, BleakClient
import asyncio



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

        start_mono = await badge.start_microphone(t=None, mode=1)

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

        await badge.stop_microphone()  # stop recording

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

    scan =await badge.get_status() # get scan status
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

    def connect(self):
        connection = BLEBadgeConnection.get_connection_to_badge(self.address)
        connection.connect()
        badge = OpenBadge(self.connection)
        print("Connected!")
        return badge


async def main():
    device_addr = sys.argv[1]

    # In Bleak, my experience is that it is rather prone to disconnection when executing many commands in one
    # context manager. Separate each command with context managers increase the rate of success.


    async with OpenBadge(0, device_addr) as badge:
        print(" connetced                         ")
        print("###################################")
        print(" Midge test                        ")

        try:
            await mic_test(badge,0)
        except:
            print("mic error")

        try:
            await mic_test(badge,1)
        except:
            print("mic error")

        try:
            await scan_test(badge)
        except:
            print("scan error")

        try:
            await imu_test(badge)
        except:
            print("imu error")
    
        try:
            await errase_mem(badge)
        except:
            print("errase memory error")


async def test_client():
    for i in range(10):
        try:
            # Measure scanning time
            scan_start = time.time()
            device = await BleakScanner.find_device_by_address("de:94:80:39:25:be", timeout=10)
            scan_time = time.time() - scan_start
            
            if device is None:
                print("Device not found during scan")
                continue
                
            # Measure connection time
            print(f"Found device in {scan_time:.2f} seconds")
            connect_start = time.time()
            async with BleakClient(device, timeout=10) as client:
                connect_time = time.time() - connect_start
                print(f"Connected in {connect_time:.2f} seconds!")

                # await client.start_notify(utils.RX_CHAR_UUID, callback=lambda sender, data: print(f"Received data: {data}"), timeout=10)
        except Exception as e:
            total_time = time.time() - scan_start
            print(f"Error after {total_time:.2f} seconds: {str(e)}")


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(test_client())