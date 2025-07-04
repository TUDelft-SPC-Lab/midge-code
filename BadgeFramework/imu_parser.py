#!/usr/bin/env python

import matplotlib.pyplot as plt
import struct
from datetime import datetime as dt
import numpy as np
import pandas as pd
import seaborn as sns
from pathlib import Path
from parser_utilities import parse_timestamps

class IMUParser(object):

    def __init__(self,filename):
        self.filename = filename
        self.path_accel = filename+'ACC_0'
        self.path_gyro = filename+'GYR_0'
        self.path_mag = filename+'MAG_0'
        self.path_rotation = filename+'ROT_0'
        self.path_scan = filename+'SCAN_0'

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
        return df

    def parse_scanner(self):
        data = []
        timestamps = []
        with open(self.path_scan, "rb") as f:
            byte = f.read()
            i = 0
            while True:
                ts_bytes = byte[0 + i:8 + i]
                data_bytes = byte[8 + i:16 + i]
                if (len(data_bytes)) == 8 and (len(ts_bytes) == 8):
                    ts = struct.unpack('<Q', ts_bytes)
                    print(struct.unpack('<B', data_bytes[0]))
                    print(struct.unpack('<B', data_bytes[1]))
                    print(struct.unpack('<B', data_bytes[2]))
                    print(struct.unpack('<B', data_bytes[3]))
                    print(struct.unpack('<B', data_bytes[4]))
                    print(struct.unpack('<B', data_bytes[5]))
                    print(struct.unpack('<B', data_bytes[6]))
                    print(struct.unpack('<B', data_bytes[7]))
                    sensor_id = (struct.unpack('<B', data_bytes[5])[0] << 8) + (struct.unpack('<B', data_bytes[4])[0])
                    rssi = struct.unpack('<b', data_bytes[3])[0] #R
                    group = (struct.unpack('<B', data_bytes[7])[0])
                    #sensor_id, rssi, group = struct.unpack('<HBB', data_bytes)
                    data.append([sensor_id, rssi, group])
                    timestamps.append(ts)
                    i = i + 16
                else:
                   break
        data_xyz = np.asarray(data)
        timestamps = np.asarray(timestamps)
        timestamps_dt = parse_timestamps(timestamps, self.path_scan)
        df = pd.DataFrame(timestamps_dt, columns=['time'])
        if data_xyz.size > 0:
            df['SensorID'] = data_xyz[:, 0]
            df['RSSI'] = data_xyz[:, 1]
            df['Group'] = data_xyz[:, 2]
        self.scan_df = df       

    def parse_accel(self):
        self.accel_df = self.parse_generic(self.path_accel)

    def parse_gyro(self):
        self.gyro_df = self.parse_generic(self.path_gyro)

    def parse_mag(self):
        self.mag_df = self.parse_generic(self.path_mag)

    def parse_rot(self):
        rotation = []
        timestamps = []
        with open(self.path_rotation, "rb") as f:
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
        timestamps_dt = parse_timestamps(timestamps, self.path_rotation)
        df = pd.DataFrame(timestamps_dt, columns=['time'])
        df['a'] = rotation_xyz[:,0]
        df['b'] = rotation_xyz[:,1]
        df['c'] = rotation_xyz[:,2]
        df['d'] = rotation_xyz[:,2]
        self.rot_df = df

    def plot_and_save(self,a,g,m):
        if a:
            fname = self.filename + '_accel.png'
            ax = self.accel_df.plot(x='time')
            fig = ax.get_figure()
            fig.savefig(fname)
        if g:
            fname = self.filename + '_gyro.png'
            ax = self.gyro_df.plot(x='time')
            fig = ax.get_figure()
            fig.savefig(fname)
        if m:
            fname = self.filename + '_mag.png'
            ax = self.mag_df.plot(x='time')
            fig = ax.get_figure()
            fig.savefig(fname)

    def save_dataframes(self,a,g,m,r,s):
        if a:
            self.accel_df.to_pickle(self.path_accel + '.pkl')
            self.accel_df.to_csv(self.path_accel + '.csv')
        if g:
            self.gyro_df.to_pickle(self.path_gyro + '.pkl')
            self.gyro_df.to_csv(self.path_gyro + '.csv')
        if m:
            self.mag_df.to_pickle(self.path_mag + '.pkl')
            self.mag_df.to_csv(self.path_mag + '.csv')
        if s:
            self.scan_df.to_pickle(self.path_scan + '.pkl')
            self.scan_df.to_csv(self.path_scan + '.csv')
        if r:
            self.rot_df.to_pickle(self.path_rotation + '.pkl')
            self.rot_df.to_csv(self.path_rotation + '.csv')

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





