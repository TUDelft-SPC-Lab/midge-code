function checkbox_plot_control
    % Sample data
    time = 0:0.1:10;
    data1 = sin(time);
    data2 = cos(time);
    data3 = tanh(time);

    % Create a figure
    fig = figure('Name', 'Checkbox Plot Control', 'Position', [100, 100, 800, 600]);

    % Plot the data and store the plot handles
    h1 = plot(time, data1, 'r-', 'DisplayName', 'sin(t)');
    hold on;
    h2 = plot(time, data2, 'g-', 'DisplayName', 'cos(t)');
    h3 = plot(time, data3, 'b-', 'DisplayName', 'tanh(t)');
    hold off;

    % Add legend
    legend('show');

    % Add labels and title
    xlabel('Time');
    ylabel('Values');
    title('Plot with Checkbox Controls');

    % Create checkboxes to control the visibility of each plot
    uicontrol('Style', 'checkbox', 'String', 'Show sin(t)', ...
              'Position', [650, 500, 120, 20], 'Value', 1, ...
              'Callback', @(src, event) toggleVisibility(src, h1));

    uicontrol('Style', 'checkbox', 'String', 'Show cos(t)', ...
              'Position', [650, 470, 120, 20], 'Value', 1, ...
              'Callback', @(src, event) toggleVisibility(src, h2));

    uicontrol('Style', 'checkbox', 'String', 'Show tanh(t)', ...
              'Position', [650, 440, 120, 20], 'Value', 1, ...
              'Callback', @(src, event) toggleVisibility(src, h3));
end

% Callback function to toggle the visibility of a plot
function toggleVisibility(src, plotHandle)
    if src.Value == 1
        plotHandle.Visible = 'on';
    else
        plotHandle.Visible = 'off';
    end
end