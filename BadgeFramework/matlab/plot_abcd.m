function x = plot_abcd(T)
    % Assuming 'T' is your table with columns 'time', 'X', 'Y', and 'Z'
    
    % Plot the data
    figure;
    plot(T.time, T.a, '-r', 'DisplayName', 'a');
    hold on;
    plot(T.time, T.b, '-g', 'DisplayName', 'b');
    plot(T.time, T.c, '-b', 'DisplayName', 'c');
    plot(T.time, T.d, '-y', 'DisplayName', 'd');
    hold off;
    
    % Add labels and title
    xlabel('Time');
    ylabel('Values');
    title('a, b, c, and d over Time');
    
    % Add legend
    legend('show');
    
    % Optional: Improve grid visibility
    grid on;

    x = 0;
end