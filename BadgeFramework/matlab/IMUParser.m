classdef IMUParser
    properties
        path_accel
        path_gyro
        path_mag
        path_rotation
        path_scan
        path_save

        accel_df
        gyro_df
        mag_df
        rot_df
        scan_df

        midge_id
        block_size
    end

    methods
        function obj = IMUParser(record_path, midge_id, block_size, local_path)
            sensor_files = get_sensor_paths(record_path);
            obj.path_accel = sensor_files.accel{1};
            obj.path_gyro = sensor_files.gyr{1};
            obj.path_mag = sensor_files.mag{1};
            obj.path_rotation = sensor_files.rotation{1};
            obj.path_scan = sensor_files.proximity{1};
            obj.path_save = local_path;
            obj.midge_id = midge_id;
            obj.block_size = block_size;
        end

        function obj = parse_accel(obj)
            obj.accel_df = obj.parse_generic(obj.path_accel, 3);
        end

        function obj = parse_gyro(obj)
            obj.gyro_df = obj.parse_generic(obj.path_gyro, 3);
        end

        function obj = parse_mag(obj)
            obj.mag_df = obj.parse_generic(obj.path_mag, 3);
        end

        function obj = parse_rot(obj)
            obj.rot_df = obj.parse_generic(obj.path_rotation, 4);
        end

        function df = parse_generic(obj, file_path, axis_num)
            fid = fopen(file_path, 'rb');
            raw_data = fread(fid);
            fclose(fid);
        
            % Define block size and calculate the number of blocks
            num_blocks = floor(length(raw_data) / obj.block_size);
            
            % Extract all blocks in one go
            blocks = reshape(raw_data(1:num_blocks * obj.block_size), ...
                obj.block_size, num_blocks);
            
            % Extract timestamps
            timestamp_bytes = blocks(1:8, :); % First 8 bytes of each block
            timestamps = double(typecast(uint8(timestamp_bytes(:)), 'uint64'));
            
            % Extract data dimensions (3 sets of 4-byte floats)
            end_ind = 8 + axis_num * 4;
            data_bytes = blocks(9:end_ind, :); % Bytes 9 to 20 for each block
            data = typecast(uint8(data_bytes(:)), 'single');
            data = reshape(data, axis_num, num_blocks)';
        
            % Create a table
            if axis_num == 3
                % accel, gyro, magnitude
                df = table(timestamps, data(:,1), data(:,2), data(:,3), ...
                    'VariableNames', {'time', 'x', 'y', 'z'});
            elseif axis_num == 4
                % rotation
                df = table(timestamps, data(:,1), data(:,2), data(:,3), ...
                    data(:,4), 'VariableNames', {'time', 'x', 'y', 'z', 'w'});
            end
            % Remove erroneous timestamps
            % df = remove_large_time_rows(df);
        
            % Convert timestamps to datetime
            df.time = datetime(df.time / 1000, 'ConvertFrom', 'posixtime');
        end

        function save_dataframes(obj, acc, gyr, mag, rot)
            if acc && ~isempty(obj.accel_df)
                obj.save_single_csv(obj.accel_df, "acc")
            end
            if gyr && ~isempty(obj.gyro_df)
                obj.save_single_csv(obj.gyro_df, "gyr")
            end
            if mag && ~isempty(obj.mag_df)
                obj.save_single_csv(obj.mag_df, "mag")
            end
            if rot && ~isempty(obj.rot_df)
                obj.save_single_csv(obj.rot_df, "rot")
            end
            mat_file = obj.path_save + obj.midge_id + "_data.mat";
            acc_data = obj.accel_df;
            gyr_data = obj.gyro_df;
            mag_data = obj.mag_df;
            rot_data = obj.rot_df;
            save(mat_file, 'acc_data', 'gyr_data', 'mag_data', 'rot_data');
        end

        function save_single_csv(obj, var, sensor_name)
            csv_file = obj.path_save + "csv/" + obj.midge_id + "_" + sensor_name + ".csv";
            writetable(var, csv_file);
        end
    end
end
