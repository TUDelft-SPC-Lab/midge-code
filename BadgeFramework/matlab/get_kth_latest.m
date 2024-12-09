function subfolder_path = get_kth_latest(folder_path, k)
    % GET_KTH_LATEST Get the path of the k-th largest subfolder based on 'y' in the subfolder names 'x_y'.
    %
    % Args:
    %   folder_path (char): Path to the main folder containing subfolders named 'x_y'.
    %   k (int): The rank of the subfolder to retrieve (1-based).
    %
    % Returns:
    %   subfolder_path (char): Path of the k-th largest subfolder based on 'y'.
    %
    % Raises:
    %   Error if 'k' is invalid or there are not enough valid subfolders.

    % Get a list of all items in the folder
    items = dir(folder_path);
    
    % Initialize a cell array to store subfolders with extracted y-values
    subfolders_with_y = {};

    % Iterate over all items
    for i = 1:length(items)
        if items(i).isdir && ~strcmp(items(i).name, '.') && ~strcmp(items(i).name, '..')
            subfolder_name = items(i).name;
            subfolder_path = fullfile(folder_path, subfolder_name);
            
            % Split the subfolder name into 'x' and 'y'
            tokens = split(subfolder_name, '_');
            if length(tokens) == 2
                try
                    y = str2double(tokens{2});
                    if ~isnan(y)
                        subfolders_with_y{end+1, 1} = y;               % Store the y-value
                        subfolders_with_y{end, 2} = subfolder_path;    % Store the subfolder path
                    end
                catch
                    % Skip subfolders that don't match the 'x_y' pattern
                end
            end
        end
    end

    % Check if there are valid subfolders
    if isempty(subfolders_with_y)
        error('No valid subfolders found in the specified folder.');
    end

    % Sort the subfolders by y in descending order
    subfolders_with_y = sortrows(subfolders_with_y, -1);

    % Validate k
    if k < 1 || k > size(subfolders_with_y, 1)
        error('Invalid value of k: %d. Must be between 1 and %d.', k, size(subfolders_with_y, 1));
    end

    % Return the path of the k-th largest subfolder
    subfolder_path = subfolders_with_y{k, 2};
end