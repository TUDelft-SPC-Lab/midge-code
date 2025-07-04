#!/usr/bin/env python

import matplotlib.pyplot as plt
import struct
import numpy as np
import pandas as pd
from parser_utilities import parse_timestamps
import os
import fnmatch


def get_sensor_files(base_dir, prefix):
    """Return a sorted list of all files in base_dir that start with prefix and have no extension."""
    return sorted([
        os.path.join(base_dir, fname)
        for fname in os.listdir(base_dir)
        if fnmatch.fnmatch(fname, prefix + '*') and not os.path.splitext(fname)[1]
    ])

class IMUParser(object):
    def __init__(self, base_dir):
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
            self.scan_dfs.append({'df': df, 'source_file': scan_file})

    def parse_generic_sensors(self, files, target_list):
        """Parse generic sensor files and append to target list."""
        for file in files:
            df = self.parse_generic(file)
            target_list.append({'df': df, 'source_file': file})

    def parse_accel(self):
        self.parse_generic_sensors(self.accel_files, self.accel_dfs)

    def parse_gyro(self):
        self.parse_generic_sensors(self.gyro_files, self.gyro_dfs)

    def parse_mag(self):
        self.parse_generic_sensors(self.mag_files, self.mag_dfs)

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
            df['d'] = rotation_xyz[:,2]  # TODO: check if this is correct
            self.rot_dfs.append({'df': df, 'source_file': rot_file})

    def plot_dataframes(self, dfs, enabled):
        """Generic function to plot dataframes."""
        if enabled and dfs:
            for df_info in dfs:
                folder = os.path.dirname(df_info['source_file'])
                basename = os.path.splitext(os.path.basename(df_info['source_file']))[0]
                fname = os.path.join(folder, f"{basename}.png")
                ax = df_info['df'].plot(x='time')
                fig = ax.get_figure()
                fig.savefig(fname)
                plt.close(fig)

    def plot_and_save(self, a, g, m):
        self.plot_dataframes(self.accel_dfs, a)
        self.plot_dataframes(self.gyro_dfs, g)
        self.plot_dataframes(self.mag_dfs, m)

    def save_dataframes_generic(self, dfs, enabled):
        """Generic function to save dataframes."""
        if enabled and dfs:
            for df_info in dfs:
                folder = os.path.dirname(df_info['source_file'])
                basename = os.path.splitext(os.path.basename(df_info['source_file']))[0]
                fname_base = os.path.join(folder, basename)
                df_info['df'].to_pickle(fname_base + '.pkl')
                df_info['df'].to_csv(fname_base + '.csv')

    def save_dataframes(self,a,g,m,r,s):
        self.save_dataframes_generic(self.accel_dfs, a)
        self.save_dataframes_generic(self.gyro_dfs, g)
        self.save_dataframes_generic(self.mag_dfs, m)
        self.save_dataframes_generic(self.scan_dfs, s)
        self.save_dataframes_generic(self.rot_dfs, r)

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
