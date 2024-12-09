% Main script to parse IMU data
midge_data_parent = "/home/zonghuan/tudelft/projects/datasets/" + ...
    "new_collection/tech_pilot_1/midge_data/";
midge_id = 54;
midge_folder = get_kth_latest(midge_data_parent + midge_id + '/', 1);

% Create IMUParser object
parser = IMUParser(midge_folder);

% Parse data
parser = parser.parse_accel();
parser = parser.parse_gyro();
parser = parser.parse_mag();
parser = parser.parse_rot();

plot_xyz(parser.accel_df);

% Save parsed data
parser.save_dataframes(true, true, true, true);

disp('Parsing and saving completed.');
