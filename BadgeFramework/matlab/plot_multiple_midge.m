function plot_multiple_midge(data, plot_options, use_mag)
    % Function to plot acc, gyr, mag, and rot data for multiple badges.
    % badge_data: a cell array where each cell contains sensor data tables for one badge.
    %
    % Example: badge_data{1}.acc_data, badge_data{1}.gyr_data, etc.

    % Define sensor types and titles
    sensor_types = {'acc', 'gyr', 'mag', 'rot'};
    sensor_titles = {'Accelerometer', 'Gyroscope', 'Magnetometer', 'Rotation'};

    % Define colors for each axis: x, y, z, w
    % Red for x, Green for y, Blue for z, Magenta for w (if applicable)
    axis_colors = {'r', 'g', 'b', 'm'};  

    % Number of badges
    num_badges = length(data);
    sensor_axes = 'xyzwuv';

    % Loop through each sensor type
    for s = 1:length(sensor_types)
        if ~plot_options(s)
            continue;
        end
        figure('Name', sensor_titles{s}, 'NumberTitle', 'off');
        
        % Loop through each badge to create a subplot for each badge's data
        for b = 1:num_badges

            % Get the current badge's sensor data
            sensor_field = [sensor_types{s}, '_data'];  % e.g., 'acc_data'
            data_single = data{b}.(sensor_field);
            
            % Extract timestamps and values
            time = data_single{:, 1};    % First column is the timestamp
            values = data_single{:, 2:end};  % Remaining columns are x, y, z, (possibly w)
            num_axes = size(values, 2);

            if use_mag
                % Compute the magnitude of the sensor data
                mag_values = sqrt(sum(values.^2, 2));
            end
            
            % Create subplot with vertical spacing
            subplot(num_badges, 1, b);
            hold on;
            if use_mag
                plot(time, mag_values, 'k-', 'DisplayName', 'Magnitude');
            else
                for a = 1:num_axes
                    % axis = axes(a);
                    plot(time, values(:, a), 'Color', axis_colors{a}, ...
                        'DisplayName', sensor_axes(a));
                end
            end
            hold off;
            
            % Add labels and legend
            ylabel(['Badge ', num2str(data{b}.midge_id)]);
            if b == 1
                title([sensor_titles{s}, ' Data']);
            end
            if b == num_badges
                xlabel('Timestamp');
            end
            legend('show');
            grid on;
        end
    end
end
