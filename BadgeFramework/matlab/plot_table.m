function plot_table(T, plot_title, fig_handle)
    % Assuming 'T' is a table where the first column is 'time' and the rest are data columns
    assert (length(T.time) == length(unique(T.time)));

    % Extract time and data
    time = T{:, 1};                % The first column is 'time'
    data = T{:, 2:end};            % All other columns contain the data to be plotted

    % Generate labels dynamically based on the number of columns
    num_series = size(data, 2);    % Number of data columns
    labels = 'xyzwuv';  % Possible labels
    plot_labels = cell(1, num_series);
    for i = 1:num_series
        plot_labels{i} = labels(i);
    end

    % Define a set of colors to cycle through
    colors = {'r', 'g', 'b', 'y', 'm', 'c', 'k'};
    num_colors = length(colors);
    
    % Check if a figure handle is provided
    if nargin < 3 || isempty(fig_handle)
        figure;  % Create a new figure if no handle is provided
    else
        figure(fig_handle);  % Use the provided figure handle
    end

    % Create the figure and plot each series
    hold on;
    for i = 1:num_series
        color = colors{mod(i - 1, num_colors) + 1};  % Cycle through colors
        plot(time, data(:, i), '-', 'Color', color, 'DisplayName', plot_labels{i});
    end
    hold off;

    % Add labels and title
    xlabel('Time');
    ylabel('Values');
    title(plot_title);

    % Add legend
    legend('show');

    % Improve grid visibility
    grid on;
end