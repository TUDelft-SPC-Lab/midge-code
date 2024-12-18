
function filteredTable = remove_large_time_rows(inputTable)
    % REMOVE_LARGE_TIME_ROWS Removes rows where the time in the first column is > 1e13.
    %
    % Args:
    %   inputTable (table): The input table where the first column contains time values.
    %
    % Returns:
    %   filteredTable (table): The table with rows removed where time > 1e13.

    % Define the threshold
    timeThreshold = 1e13;

    % Get the time values from the first column
    timeValues = inputTable{:, 1};

    % Create a logical index for rows where time <= 1e13
    validRows = timeValues <= timeThreshold;

    % Filter the table using the valid rows
    filteredTable = inputTable(validRows, :);
end