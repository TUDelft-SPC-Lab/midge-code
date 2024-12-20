function checkbox_plot_control
    % Sample data
    time = 0:0.1:10;
    data1 = sin(time);
    data2 = cos(time);
    data3 = tanh(time);

    % Create a figure with a resize callback
    fig = figure;
    set(fig, 'Name', 'Checkbox Plot Control', 'Position', ...
        [100, 100, 800, 600], 'ResizeFcn', @resizeCheckBoxes);


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
    cb1 = uicontrol('Style', 'checkbox', 'String', 'Show sin(t)', ...
                    'Value', 1, 'Callback', @(src, event) toggleVisibility(src, h1));
    cb2 = uicontrol('Style', 'checkbox', 'String', 'Show cos(t)', ...
                    'Value', 1, 'Callback', @(src, event) toggleVisibility(src, h2));
    cb3 = uicontrol('Style', 'checkbox', 'String', 'Show tanh(t)', ...
                    'Value', 1, 'Callback', @(src, event) toggleVisibility(src, h3));

    % Store the checkboxes in a struct for easy access during resizing
    checkboxes = struct('cb1', cb1, 'cb2', cb2, 'cb3', cb3);
    setappdata(fig, 'checkboxes', checkboxes);

    % Initial positioning of the checkboxes
    resizeCheckBoxes(fig);
end

% Callback function to toggle the visibility of a plot
function toggleVisibility(src, plotHandle)
    if src.Value == 1
        plotHandle.Visible = 'on';
    else
        plotHandle.Visible = 'off';
    end
end

% Resize function to adjust the position of the checkboxes
function resizeCheckBoxes(fig)
    % Get figure size
    figPos = fig.Position;
    figWidth = figPos(3);
    figHeight = figPos(4);

    % Checkbox width and height
    cbWidth = 120;
    cbHeight = 20;
    spacing = 10;  % Spacing between checkboxes

    % Get the checkboxes from the figure's app data
    checkboxes = getappdata(fig, 'checkboxes');

    % Set positions for each checkbox (top-right corner)
    set(checkboxes.cb1, 'Position', [figWidth - cbWidth - spacing, figHeight - cbHeight - spacing, cbWidth, cbHeight]);
    set(checkboxes.cb2, 'Position', [figWidth - cbWidth - spacing, figHeight - 2 * (cbHeight + spacing), cbWidth, cbHeight]);
    set(checkboxes.cb3, 'Position', [figWidth - cbWidth - spacing, figHeight - 3 * (cbHeight + spacing), cbWidth, cbHeight]);
end
