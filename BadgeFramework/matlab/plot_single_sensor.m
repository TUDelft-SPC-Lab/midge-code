function plot_single_sensor(T, fig_handle, use_mag)
    axis_colors = 'rgbymck';  
    sensor_axes = 'xyzwuv';

    time = T{:, 1};    % First column is the timestamp
    values = T{:, 2:end};  % Remaining columns are x, y, z, (possibly w)
    num_axes = size(values, 2);
    assert (length(T.time) == length(unique(T.time)));
    if use_mag
        % Compute the magnitude of the sensor data
        mag_values = sqrt(sum(values.^2, 2));
    end
    
    % Create subplot with vertical spacing
    figure(fig_handle);
    hold on;
    if use_mag
        plot(time, mag_values, 'k-', 'DisplayName', 'Magnitude');
    else
        for a = 1:num_axes
            plot(time, values(:, a), 'Color', axis_colors(a), ...
                'DisplayName', sensor_axes(a));
        end
    end
    hold off;
end