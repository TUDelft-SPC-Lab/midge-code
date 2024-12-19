clear variables; close all;

% Main script to parse IMU data
% midge_data_parent = "/home/zonghuan/tudelft/projects/datasets/" + ...
%     "new_collection/tech_pilot_1/midge_data/";
midge_data_parent = "C:/Users/zongh/OneDrive - Delft University of Technology" + ...
    "/tudelft/projects/dataset_collection/tech_pilot_1/midge_data/";
midge_id = 12;
midge_folder = get_kth_latest(midge_data_parent + midge_id + '/', 1);

bs24 = [12, 19, 24, 32, 33, 34, 35, 37, 45, 48, 54, 57, 59];
bs32 = [7, 24, 25, 28, 29];
problematic = [19, 34, 35, 59];

if any(midge_id==bs24)
    block_size = 24;
elseif any(midge_id==bs32)
    block_size = 32;
end

% Create IMUParser object
parser = IMUParser(midge_folder, block_size);

% Parse data
parser = parser.parse_accel();
parser = parser.parse_gyro();
parser = parser.parse_mag();
parser = parser.parse_rot();

plot_table(parser.accel_df, 'accelerometer');
plot_table(parser.gyro_df, 'gyro');
% plot_table(parser.mag_df, 'magnitude');
% plot_table(parser.rot_df, 'rotation');

% Save parsed data
% parser.save_dataframes(true, true, true, true);
disp('Parsing and saving completed.');
