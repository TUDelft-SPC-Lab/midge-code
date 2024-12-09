import matplotlib.pyplot as plt
import struct
from datetime import datetime as dt
import numpy as np
import pandas as pd
import seaborn as sns
import argparse
from audio_parser_V0 import get_kth_latest
import os

def get_sensor_paths(folder_path: str) -> dict:
    """
    Returns 5 lists of file names that end with specific suffixes.

    Args:
        folder_path (str): Path to the folder.

    Returns:
        tuple: Five lists of file names matching the suffixes:
               - "_accel"
               - "_gyr"
               - "mag"
               - "_rotation"
               - "_proximity"
    """
    # Initialize lists for each suffix
    files = {
        'accel': [], 'gyr': [], 'mag': [], 'rotation': [], 'proximity': []
    }

    # Iterate through all files in the folder
    for file_name in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, file_name)):
            if file_name.endswith("_accel"):
                files['accel'].append(file_name)
            elif file_name.endswith("_gyr"):
                files['gyr'].append(file_name)
            elif file_name.endswith("mag"):
                files['mag'].append(file_name)
            elif file_name.endswith("_rotation"):
                files['rotation'].append(file_name)
            elif file_name.endswith("_proximity"):
                files['proximity'].append(file_name)

    check_multiple_sensor_files(files)
    return files

def check_multiple_sensor_files(files):
    for file_list in files.values():
        if len(file_list) == 0:
            print("Warning: No sensor files found!")
        if len(file_list) > 1:
            print('Warning: Multiple sensor files detected!')

class IMUParser(object):
    def __init__(self, record_path):
        sensor_files = get_sensor_paths(record_path)
        self.record_path = record_path
        self.path_accel = os.path.join(record_path, sensor_files['accel'][0])
        self.path_gyro = os.path.join(record_path, sensor_files['gyr'][0])
        self.path_mag = os.path.join(record_path, sensor_files['mag'][0])
        self.path_rotation = os.path.join(record_path, sensor_files['rotation'][0])
        self.path_scan = os.path.join(record_path, sensor_files['proximity'][0])

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
                    i = i + 24
                else:
                    break
        self.check_ts(timestamps)

        data_xyz = np.asarray(data)
        timestamps = np.asarray(timestamps)
        timestamps_dt = [dt.fromtimestamp(float(x)/1000) for x in timestamps]
        df = pd.DataFrame(timestamps_dt, columns=['time'])
        df['X'] = data_xyz[:,0]
        df['Y'] = data_xyz[:,1]
        df['Z'] = data_xyz[:,2]
        return df

    @staticmethod
    def check_ts(nums, thres=1e13):
        timestamps = [x[0] for x in nums]
        results = [(i, f"{num:.0f}") for i, num in enumerate(timestamps) if num > thres]
        timestamp_good = [x for x in timestamps if x < 1e13]
        good_diff = [timestamp_good[x + 1] - timestamp_good[x] for x in range(len(timestamp_good) - 2)]
        d = [x for x in good_diff if x > 20 or x < 10]
        c = 9

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
        timestamps_dt = [dt.fromtimestamp(float(x) / 1000) for x in timestamps]
        df = pd.DataFrame(timestamps_dt, columns=['time'])
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
                    i = i + 32
                else:
                    break
        rotation_xyz = np.asarray(rotation)
        timestamps = np.asarray(timestamps)
        timestamps_dt = [dt.fromtimestamp(float(x)/1000) for x in timestamps]
        df = pd.DataFrame(timestamps_dt, columns=['time'])
        df['a'] = rotation_xyz[:,0]
        df['b'] = rotation_xyz[:,1]
        df['c'] = rotation_xyz[:,2]
        df['d'] = rotation_xyz[:,2]
        self.rot_df = df

    def plot_and_save(self,a,g,m):
        if a:
            fname = self.record_path + '_accel.png'
            ax = self.accel_df.plot(x='time')
            fig = ax.get_figure()
            fig.savefig(fname)
        if g:
            fname = self.record_path + '_gyro.png'
            ax = self.gyro_df.plot(x='time')
            fig = ax.get_figure()
            fig.savefig(fname)
        if m:
            fname = self.record_path + '_mag.png'
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

def parse_imu(fn,acc,mag,gyr,rot,plot,scan):
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

def get_default_file_path():
    midge_data_parent = "/home/zonghuan/tudelft/projects/datasets/new_collection/tech_pilot_1/midge_data/"
    midge_id = 54
    return get_kth_latest(os.path.join(midge_data_parent, str(midge_id)), 1)

def main():
    parser = argparse.ArgumentParser(description='Parser for the IMU data obtained from Minge Midges\
        (Acceleration, Gyroscope, Magnetometer, Rotation)')
    parser.add_argument('--fn', default=get_default_file_path(), help='Please enter the path to the file')
    parser.add_argument('--acc', default=True, type=str2bool, help='Check to parse and save acceleration data')
    parser.add_argument('--mag', default=True, type=str2bool, help='Check to parse and save magnetometer data')
    parser.add_argument('--gyr', default=True, type=str2bool, help='Check to parse and save gyroscope data')
    parser.add_argument('--scan', default=True, type=str2bool, help='Check to parse and save scan data')
    parser.add_argument('--rot', default=True, type=str2bool, help='Check to parse and save rotation data')
    parser.add_argument('--plot', default=True, type=str2bool, help='Check to plot the parsed data')
    args = parser.parse_args()
    parse_imu(fn=args.fn, acc=args.acc, mag=args.mag, gyr=args.gyr, rot=args.rot, plot=args.plot, scan=args.scan)

if __name__ == '__main__':
    main()
    # Example command
    # python ./imu_parser_V0.py --fn ../midge_0_files/ --scan TRUE --acc TRUE --mag TRUE --rot TRUE --gyr TRUE --rot TRUE --plot True
