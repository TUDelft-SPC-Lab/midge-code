function plot_multiple_midge(data, plot_options, use_mag)
    % Function to plot acc, gyr, mag, and rot data for multiple badges.
    % badge_data: a cell array where each cell contains sensor data tables for one badge.
    %
    % Example: badge_data{1}.acc_data, badge_data{1}.gyr_data, etc.

    % Define sensor types and titles
    midge_info = struct();
    midge_info.ids = {};
    for k=1:length(data)
        midge_info.ids{k} = data{k}.midge_id;
        midge_info.names{k} = "Midge " + data{k}.midge_id;
    end
    midge_info.plot_options = plot_options.midge;
    midge_info.plot_num_all = length(data);

    sensor_info = struct();
    sensor_info.types = {'acc', 'gyr', 'mag', 'rot'};
    sensor_info.names = {'Accelerometer', 'Gyro', 'Magnitude', 'Rotation'};
    sensor_info.plot_options = plot_options.sensor;
    sensor_info.plot_num_all = length(sensor_info.types);


    if plot_options.display == "midge"
        s1 = midge_info;
        s2 = sensor_info;
    elseif plot_options.display == "sensor"
        s1 = sensor_info;
        s2 = midge_info;
    else
        error("Invalid display option");
    end
    
    subplot_ids = find(s2.plot_options == 1);
    % Loop through each sensor type
    for k1 = 1:s1.plot_num_all
        if ~s1.plot_options(k1)
            continue;
        end
        fig = figure('Name', s1.names{k1}, 'NumberTitle', 'off');
        
        % Loop through each badge to create a subplot for each badge's data
        for k2 = 1:s2.plot_num_all
            if ~s2.plot_options(k2)
                continue;
            end
            
            % Get the current midge's sensor data
            if plot_options.display == "midge"
                sensor_field = [s2.types{k2}, '_data'];
                data_single = data{k1}.(sensor_field);
            elseif plot_options.display == "sensor"
                sensor_field = [s1.types{k1}, '_data'];
                data_single = data{k2}.(sensor_field);
            else
                error("Invalid display option");
            end
            subplot(length(subplot_ids), 1, k2);
            plot_single_sensor(data_single, fig, use_mag);
            
            % Add labels and legend
            ylabel(s2.names(k2));
            if k2 == subplot_ids(1)
                title(s1.names{k1});
            end
            if k2 == subplot_ids(end)
                xlabel('Timestamp');
            end
            legend('show');
            grid on;
        end
    end
end
