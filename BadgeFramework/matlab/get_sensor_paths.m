function sensor_files = get_sensor_paths(folder_path)
    % Returns a struct containing lists of file names matching specific suffixes.
    sensor_files.accel = {};
    sensor_files.gyr = {};
    sensor_files.mag = {};
    sensor_files.rotation = {};
    sensor_files.proximity = {};

    files = dir(folder_path);
    for i = 1:length(files)
        if ~files(i).isdir
            file_name = files(i).name;
            if endsWith(file_name, '_accel')
                sensor_files.accel{end+1} = fullfile(folder_path, file_name);
            elseif endsWith(file_name, '_gyr')
                sensor_files.gyr{end+1} = fullfile(folder_path, file_name);
            elseif endsWith(file_name, 'mag')
                sensor_files.mag{end+1} = fullfile(folder_path, file_name);
            elseif endsWith(file_name, '_rotation')
                sensor_files.rotation{end+1} = fullfile(folder_path, file_name);
            elseif endsWith(file_name, '_proximity')
                sensor_files.proximity{end+1} = fullfile(folder_path, file_name);
            end
        end
    end

    check_multiple_sensor_files(sensor_files);
end

function check_multiple_sensor_files(files)
    fields = fieldnames(files);
    for i = 1:numel(fields)
        file_list = files.(fields{i});
        if isempty(file_list)
            warning('No %s sensor files found!', fields{i});
        elseif length(file_list) > 1
            warning('Multiple %s sensor files detected!', fields{i});
        end
    end
end
