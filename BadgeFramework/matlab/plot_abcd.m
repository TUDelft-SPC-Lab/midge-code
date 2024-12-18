% function plot_abcd(T, plot_title)
%     % Assuming 'T' is your table with columns 'time', 'X', 'Y', and 'Z'
% 
%     % Plot the data
%     figure;
%     plot(T.time, T.a, '-r', 'DisplayName', 'a');
%     hold on;
%     plot(T.time, T.b, '-g', 'DisplayName', 'b');
%     plot(T.time, T.c, '-b', 'DisplayName', 'c');
%     plot(T.time, T.d, '-y', 'DisplayName', 'd');
%     hold off;
% 
%     % Add labels and title
%     xlabel('Time');
%     ylabel('Values');
%     title(plot_title);
% 
%     % Add legend
%     legend('show');
% 
%     % Optional: Improve grid visibility
%     grid on;
% end