function x = plot_xyz(T)
    % Assuming 'T' is your table with columns 'time', 'X', 'Y', and 'Z'
    
    % Plot the data
    figure;
    plot(T.time, T.X, '-r', 'DisplayName', 'X');
    hold on;
    plot(T.time, T.Y, '-g', 'DisplayName', 'Y');
    plot(T.time, T.Z, '-b', 'DisplayName', 'Z');
    hold off;
    
    % Add labels and title
    xlabel('Time');
    ylabel('Values');
    title('X, Y, and Z over Time');
    
    % Add legend
    legend('show');
    
    % Optional: Improve grid visibility
    grid on;

    x = 0;
end