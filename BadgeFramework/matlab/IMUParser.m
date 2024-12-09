classdef IMUParser
    properties
        path_accel
        path_gyro
        path_mag
        path_rotation
        path_scan

        accel_df
        gyro_df
        mag_df
        rot_df
        scan_df
    end

    methods
        function obj = IMUParser(record_path)
            sensor_files = get_sensor_paths(record_path);
            obj.path_accel = sensor_files.accel{1};
            obj.path_gyro = sensor_files.gyr{1};
            obj.path_mag = sensor_files.mag{1};
            obj.path_rotation = sensor_files.rotation{1};
            obj.path_scan = sensor_files.proximity{1};
        end

        function obj = parse_accel(obj)
            obj.accel_df = parse_generic(obj.path_accel);
        end

        function obj = parse_gyro(obj)
            obj.gyro_df = parse_generic(obj.path_gyro);
        end

        function obj = parse_mag(obj)
            obj.mag_df = parse_generic(obj.path_mag);
        end

        function obj = parse_rot(obj)
            fid = fopen(obj.path_rotation, 'rb');
            raw_data = fread(fid);
            fclose(fid);
            
            block_size = 24;
        
            % Define block size and calculate the number of blocks
            num_blocks = floor(length(raw_data) / block_size);
            
            % Extract all blocks in one go
            blocks = reshape(raw_data(1:num_blocks * block_size), block_size, num_blocks);
            
            % Extract timestamps
            timestamp_bytes = blocks(1:8, :); % First 8 bytes of each block
            timestamps = double(typecast(uint8(timestamp_bytes(:)), 'uint64'));
            
            % Extract data dimensions (4 sets of 4-byte floats)
            data_bytes = blocks(9:24, :); % Bytes 9 to 24 for each block
            data_flat = typecast(uint8(data_bytes(:)), 'single');
            data = reshape(data_flat, 4, num_blocks)';
        
            % Convert timestamps to datetime
            timestamps_dt = datetime(timestamps / 1000, 'ConvertFrom', 'posixtime');
        
            % Create a table
            obj.rot_df = table(timestamps, data(:,1), data(:,2), data(:,3), ...
                data(:,4), 'VariableNames', {'time', 'a', 'b', 'c', 'd'});

            obj.rot_df = remove_large_time_rows(obj.rot_df);
        end

        function save_dataframes(obj, acc, gyr, mag, rot)
            if acc && ~isempty(obj.accel_df)
                writetable(obj.accel_df, [obj.path_accel, '.csv']);
                save([obj.path_accel, '.mat'], 'obj.accel_df');
            end
            if gyr && ~isempty(obj.gyro_df)
                writetable(obj.gyro_df, [obj.path_gyro, '.csv']);
                save([obj.path_gyro, '.mat'], 'obj.gyro_df');
            end
            if mag && ~isempty(obj.mag_df)
                writetable(obj.mag_df, [obj.path_mag, '.csv']);
                save([obj.path_mag, '.mat'], 'obj.mag_df');
            end
            if rot && ~isempty(obj.rot_df)
                writetable(obj.rot_df, [obj.path_rotation, '.csv']);
                save([obj.path_rotation, '.mat'], 'obj.rot_df');
            end
        end
    end
end
