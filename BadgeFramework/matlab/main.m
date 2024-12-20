clear variables; close all;

% Main script to parse IMU data

block_sizes = zeros(1, 100);
bs24 = [12, 19, 24, 32, 33, 34, 35, 37, 45, 48, 54, 57, 59];
bs32 = [7, 24, 25, 28, 29];
problematic = [19, 34, 35, 59];
block_sizes(bs24) = 24;
block_sizes(bs32) = 32;
good_midges = setdiff(union(bs24, bs32), problematic);
local_path = "./local/";

%% save data to mat and csv
% for k=good_midges
%     save_imu_data(block_sizes, k, local_path);
% end

%% plot
midges = [7, 12, 25, 48];
data = cell(1, length(midges));
for k=1:length(midges)
    midge_id = midges(k);
    data{k} = load(local_path + midge_id + "_data.mat");
    % remove large timestamps
    data{k} = filter_midge_data(data{k});
    data{k}.midge_id = midge_id;
end

plot_options = struct();
plot_options.midge = [1, 0, 0, 0];
plot_options.sensor = [1, 1, 1, 1];
plot_options.display = "midge";
plot_multiple_midge(data, plot_options, false);
% plot_single_midge(data{1}.acc_data, '44rr');

%% functions
function filteredData = filter_midge_data(midge)
    filteredData.acc_data = remove_large_time_rows(midge.acc_data);
    filteredData.gyr_data = remove_large_time_rows(midge.gyr_data);
    filteredData.mag_data = remove_large_time_rows(midge.mag_data);
    filteredData.rot_data = remove_large_time_rows(midge.rot_data);
end

function data_folder = get_data_folder()
    if ispc
        data_folder = "C:/Users/zongh/OneDrive - Delft University of " + ...
            "Technology/tudelft/projects/dataset_collection/tech_pilot_1/midge_data/";
    elseif isunix
        data_folder = "/home/zonghuan/tudelft/projects/datasets/" + ...
            "new_collection/tech_pilot_1/midge_data/";
    end
end

function save_imu_data(block_sizes, midge_id, local_path)
    midge_data_parent = get_data_folder();
    midge_folder = get_kth_latest(midge_data_parent + midge_id + "/", 1);

    block_size = block_sizes(midge_id);

    % Create IMUParser object
    parser = IMUParser(midge_folder, midge_id, block_size, local_path);
    
    % Parse data
    parser = parser.parse_accel();
    parser = parser.parse_gyro();
    parser = parser.parse_mag();
    parser = parser.parse_rot();

    parser.save_dataframes(true, true, true, true);
    disp("Parsing and saving completed " + midge_id);

end