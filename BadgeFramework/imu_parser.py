#!/usr/bin/env python

import matplotlib.pyplot as plt
import struct
from datetime import datetime as dt
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path
from parser_utilities import parse_timestamps
import os
import re
import fnmatch

def sanitize_folder(folder):
    # Only sanitize the last part (the folder name)
    return re.sub(r'[\\/*?:"<>|]', "", folder)

def sanitize_filename(name):
    # Remove invalid characters for Windows filenames
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_sensor_files(base_dir, prefix):
    """Return a sorted list of all files in base_dir that start with prefix."""
    return sorted([
        os.path.join(base_dir, fname)
        for fname in os.listdir(base_dir)
        if fnmatch.fnmatch(fname, prefix + '*')
    ])

def extract_number_from_filename(filename, prefix):
    # filename: full path or just the file name
    # prefix: e.g., 'ACC_'
    basename = os.path.basename(filename)
    match = re.match(r'^' + re.escape(prefix) + r'(\d+)', basename)
    if match:
        return match.group(1)
    return None

class IMUParser(object):
    def __init__(self,filename):
        self.filename = filename
        # Remove trailing slash/backslash
        fn = filename.rstrip('/\\')

        # Split the path into head and tail
        head, tail = os.path.split(fn)
        # Sanitize only the last folder name
        tail = sanitize_folder(tail)
        # Rebuild the full path
        base_dir = os.path.join(head, tail)

        # Suppose you want to save in the same directory as your data file
        self.filename = base_dir

        self.accel_files = get_sensor_files(base_dir, 'ACC_')
        self.gyro_files = get_sensor_files(base_dir, 'GYR_')
        self.mag_files = get_sensor_files(base_dir, 'MAG_')
        self.rotation_files = get_sensor_files(base_dir, 'ROT_')
        self.scan_files = get_sensor_files(base_dir, 'SCAN_')

        self.accel_dfs = []
        self.gyro_dfs = []
        self.mag_dfs = []
        self.rot_dfs = []
        self.scan_dfs = []

    def parse_generic(self,sensorname):
        data = []
        timestamps = []
        with open(sensorname, "rb") as f:
            byte = f.read()
            i=0
            while True:
                ts_bytes = byte[0+i:8+i]
                data_bytes = byte[8+i:20+i]
                if (len(data_bytes)) == 12 and (len(ts_bytes) == 8):
                    ts = struct.unpack('<Q',ts_bytes)
                    x,y,z = struct.unpack('<fff', data_bytes)
                    data.append([x,y,z])
                    timestamps.append(ts)
                    i = i + 24 # 8 timestamp + 12 data + 4 padding
                else:
                    break
        data_xyz = np.asarray(data)
        timestamps = np.asarray(timestamps)
        timestamps_dt = parse_timestamps(timestamps, sensorname)
        df = pd.DataFrame(timestamps_dt, columns=['time'])
        df['X'] = data_xyz[:,0]
        df['Y'] = data_xyz[:,1]
        df['Z'] = data_xyz[:,2]
        df.attrs['sensor_number'] = extract_number_from_filename(sensorname, 'ACC_')
        df.attrs['source_file'] = sensorname
        return df

    def parse_scanner(self):
        for scan_file in self.scan_files:
            data = []
            timestamps = []
            with open(scan_file, "rb") as f:
                byte = f.read()
                i = 0
                while True:
                    ts_bytes = byte[i : i + 8]
                    data_bytes = byte[i + 8 : i + 16]
                    if len(data_bytes) == 8 and len(ts_bytes) == 8:
                        ts = struct.unpack("<Q", ts_bytes)
                        sensor_id = struct.unpack("<H", data_bytes[0:2])[0]
                        group = struct.unpack("<b", data_bytes[2:3])[0]
                        rssi = struct.unpack("<b", data_bytes[3:4])[0]
                        data.append([sensor_id, rssi, group])
                        timestamps.append(ts)
                        i = i + 16
                    else:
                        break

            data_xyz = np.asarray(data)
            timestamps = np.asarray(timestamps)
            timestamps_dt = parse_timestamps(timestamps, scan_file)
            df = pd.DataFrame(timestamps_dt, columns=['time'])
            if data_xyz.size > 0:
                df['SensorID'] = data_xyz[:, 0]
                df['RSSI'] = data_xyz[:, 1]
                df['Group'] = data_xyz[:, 2]
            x = extract_number_from_filename(scan_file, 'SCAN_')
            self.scan_dfs.append({'df': df, 'sensor_number': x, 'source_file': scan_file})

    def parse_accel(self):
        for acc_file in self.accel_files:
            x = extract_number_from_filename(acc_file, 'ACC_')
            df = self.parse_generic(acc_file)
            self.accel_dfs.append({'df': df, 'sensor_number': x, 'source_file': acc_file})

    def parse_gyro(self):
        for gyro_file in self.gyro_files:
            x = extract_number_from_filename(gyro_file, 'GYR_')
            df = self.parse_generic(gyro_file)
            self.gyro_dfs.append({'df': df, 'sensor_number': x, 'source_file': gyro_file})

    def parse_mag(self):
        for mag_file in self.mag_files:
            x = extract_number_from_filename(mag_file, 'MAG_') 
            df = self.parse_generic(mag_file)
            self.mag_dfs.append({'df': df, 'sensor_number': x, 'source_file': mag_file})

    def parse_rot(self):
        for rot_file in self.rotation_files:
            rotation = []
            timestamps = []
            with open(rot_file, "rb") as f:
                byte = f.read()
                i=0
                while True:
                    ts_bytes = byte[0+i:8+i]
                    rot_bytes = byte[8+i:24+i]
                    if (len(rot_bytes)) == 16 and (len(ts_bytes) == 8):
                        ts = struct.unpack('<Q',ts_bytes)
                        q1,q2,q3,q4 = struct.unpack('<ffff', rot_bytes)
                        rotation.append([q1,q2,q3,q4])
                        timestamps.append(ts)
                        i = i + 24
                    else:
                        break
            rotation_xyz = np.asarray(rotation)
            timestamps = np.asarray(timestamps)
            timestamps_dt = parse_timestamps(timestamps, rot_file)
            df = pd.DataFrame(timestamps_dt, columns=['time'])
            df['a'] = rotation_xyz[:,0]
            df['b'] = rotation_xyz[:,1]
            df['c'] = rotation_xyz[:,2]
            df['d'] = rotation_xyz[:,2]
            x = extract_number_from_filename(rot_file, 'ROT_')
            self.rot_dfs.append({'df': df, 'sensor_number': x, 'source_file': rot_file})

    def plot_and_save(self, a, g, m):
        if a and self.accel_dfs:
            for acc_info in self.accel_dfs:
                sensor_number = acc_info.get('sensor_number', 'unknown')
                fname = f"{self.filename}_accel_{sensor_number}.png"
                ax = acc_info['df'].plot(x='time')
                fig = ax.get_figure()
                fig.savefig(fname)
                plt.close(fig)
        if g and self.gyro_dfs:
            for gyro_info in self.gyro_dfs:
                sensor_number = gyro_info.get('sensor_number', 'unknown')
                fname = f"{self.filename}_gyro_{sensor_number}.png"
                ax = gyro_info['df'].plot(x='time')
                fig = ax.get_figure()
                fig.savefig(fname)
                plt.close(fig)
        if m and self.mag_dfs:
            for mag_info in self.mag_dfs:
                sensor_number = mag_info.get('sensor_number', 'unknown')
                fname = f"{self.filename}_mag_{sensor_number}.png"
                ax = mag_info['df'].plot(x='time')
                fig = ax.get_figure()
                fig.savefig(fname)
                plt.close(fig)

    def save_dataframes(self,a,g,m,r,s):
        if a:
            for acc_info in self.accel_dfs:
                x = acc_info['sensor_number']
                folder = os.path.dirname(acc_info['source_file'])
                fname_base = os.path.join(folder, 'accel_' + str(x))
                acc_info['df'].to_pickle(fname_base + '.pkl')
                acc_info['df'].to_csv(fname_base + '.csv')
        if g:
            for gyro_info in self.gyro_dfs:
                x = gyro_info['sensor_number']
                folder = os.path.dirname(gyro_info['source_file'])
                fname_base = os.path.join(folder, 'gyro_' + str(x))
                gyro_info['df'].to_pickle(fname_base + '.pkl')
                gyro_info['df'].to_csv(fname_base + '.csv')
        if m:
            for mag_info in self.mag_dfs:
                x = mag_info['sensor_number']
                folder = os.path.dirname(mag_info['source_file'])
                fname_base = os.path.join(folder, 'mag_' + str(x))
                mag_info['df'].to_pickle(fname_base + '.pkl')
                mag_info['df'].to_csv(fname_base + '.csv')
        if s:
            for scan_info in self.scan_dfs:
                x = scan_info['sensor_number']
                folder = os.path.dirname(scan_info['source_file'])
                fname_base = os.path.join(folder, 'scan_' + str(x))
                scan_info['df'].to_pickle(fname_base + '.pkl')
                scan_info['df'].to_csv(fname_base + '.csv')
        if r:
            for rot_info in self.rot_dfs:
                x = rot_info['sensor_number']
                folder = os.path.dirname(rot_info['source_file'])
                fname_base = os.path.join(folder, 'rot_' + str(x))
                rot_info['df'].to_pickle(fname_base + '.pkl')
                rot_info['df'].to_csv(fname_base + '.csv')

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main(fn,acc,mag,gyr,rot,plot,scan):
    parser = IMUParser(fn)
    if acc:
        parser.parse_accel()
    if mag:
        parser.parse_mag()
    if gyr:
        parser.parse_gyro()
    if rot:
        parser.parse_rot()
    if scan:
        parser.parse_scanner()
    parser.save_dataframes(acc,mag,gyr,rot,scan)
    if plot:
        parser.plot_and_save(acc,mag,gyr)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parser for the IMU data obtained from Minge Midges\
    (Acceleration, Gyroscope, Magnetometer, Rotation)')
    parser.add_argument('--fn', required=True,help='Please enter the path to the file')
    parser.add_argument('--acc', default=True,type=str2bool ,help='Check to parse and save acceleration data')
    parser.add_argument('--mag', default=True,type=str2bool ,help='Check to parse and save magnetometer data')
    parser.add_argument('--gyr', default=True,type=str2bool,help='Check to parse and save gyroscope data')
    parser.add_argument('--scan', default=True,type=str2bool,help='Check to parse and save scan data')
    parser.add_argument('--rot', default=True,type=str2bool ,help='Check to parse and save rotation data')
    parser.add_argument('--plot', default=True,type=str2bool ,help='Check to plot the parsed data')
    args = parser.parse_args()
    main(fn=args.fn, acc=args.acc, mag=args.mag, gyr=args.gyr, rot=args.rot, plot=args.plot, scan=args.scan)

    # Example command
    # python ./imu_parser.py --fn ../midge_0_files/ --scan TRUE --acc TRUE --mag TRUE --rot TRUE --gyr TRUE --rot TRUE --plot True
    # on windows, use python imu_parser.py --fn 'C:\\user\\midge_0_files\\' --scan ..., use single quotes and double backslashes
