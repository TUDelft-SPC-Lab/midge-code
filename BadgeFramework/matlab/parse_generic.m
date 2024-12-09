function df = parse_generic(file_path)

    fid = fopen(file_path, 'rb');
    raw_data = fread(fid);
    fclose(fid);
    
    block_size = 24;

    % Define block size and calculate the number of blocks
    num_blocks = floor(length(raw_data) / block_size);
    
    % Extract all blocks in one go
    blocks = reshape(raw_data(1:num_blocks * block_size), block_size, num_blocks);
    
    % Extract timestamps
    timestamp_bytes = blocks(1:8, :); % First 8 bytes of each block
    timestamps = double(typecast(uint8(timestamp_bytes(:)), 'uint64'));
    
    % Extract data dimensions (3 sets of 4-byte floats)
    data_bytes = blocks(9:20, :); % Bytes 9 to 20 for each block
    data_flat = typecast(uint8(data_bytes(:)), 'single');
    data = reshape(data_flat, 3, num_blocks)';


    % Create a table
    df = table(timestamps, data(:,1), data(:,2), data(:,3), ...
               'VariableNames', {'time', 'X', 'Y', 'Z'});
    
    % Remove erroneous timestamps
    df = remove_large_time_rows(df);

    % Convert timestamps to datetime
    df.time = datetime(df.time / 1000, 'ConvertFrom', 'posixtime');
end
