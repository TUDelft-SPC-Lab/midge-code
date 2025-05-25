#include "file_download_lib.h"
#include "protocol_messages.h"
#include "ff.h"
#include "nrf_log.h"
#include <string.h>

static FIL download_file;
static uint32_t current_file_size = 0;
static uint32_t current_position = 0;
static char current_filename[MAX_FILENAME_LENGTH];
static bool download_active = false;

static uint32_t calculate_crc32(const uint8_t *data, size_t length);

ret_code_t list_files_handler(ListFilesRequest *request, ListFilesResponse *response)
{
    DIR dir;
    FILINFO fno;
    FRESULT ff_result;
    uint8_t file_index = 0;
    uint8_t current_index = 0;
    uint8_t total_files = 0;

    ff_result = f_opendir(&dir, "/");
    if (ff_result != FR_OK) {
        NRF_LOG_ERROR("Failed to open root directory: %d", ff_result);
        return NRF_ERROR_NOT_FOUND;
    }

    memset(response, 0, sizeof(ListFilesResponse));
    response->header.start_index = request->start_index;

    do {
        ff_result = f_readdir(&dir, &fno);
        if (ff_result == FR_OK && fno.fname[0]) {
            if (!(fno.fattrib & AM_DIR)) { // Only process files, not directories
                total_files++;
                
                if (current_index >= request->start_index && file_index < request->max_files && file_index < 3) {
                    strncpy(response->files[file_index].filename, fno.fname, MAX_FILENAME_LENGTH - 1);
                    response->files[file_index].filename[MAX_FILENAME_LENGTH - 1] = '\0';
                    response->files[file_index].file_size = fno.fsize;
                    response->files[file_index].timestamp = fno.fdate;
                    file_index++;
                }
                current_index++;
            }
        }
    } while (ff_result == FR_OK && fno.fname[0]);

    response->header.file_count = file_index;
    response->header.total_files = total_files;
    f_closedir(&dir);

    return NRF_SUCCESS;
}

ret_code_t start_download_handler(StartDownloadRequest *request, StartDownloadResponse *response)
{
    FRESULT ff_result;

    if (download_active) {
        f_close(&download_file);
        download_active = false;
    }

    ff_result = f_open(&download_file, request->filename, FA_READ);
    if (ff_result != FR_OK) {
        NRF_LOG_ERROR("Failed to open file for download: %s, error: %d", request->filename, ff_result);
        response->success = 0;
        return NRF_SUCCESS;
    }

    current_file_size = f_size(&download_file);
    current_position = 0;
    strncpy(current_filename, request->filename, MAX_FILENAME_LENGTH - 1);
    download_active = true;

    response->file_size = current_file_size;
    response->total_chunks = (current_file_size + DOWNLOAD_CHUNK_SIZE - 1) / DOWNLOAD_CHUNK_SIZE;
    response->success = 1;

    NRF_LOG_INFO("Download started for file: %s, size: %u bytes, total chunks: %u", 
                 current_filename, current_file_size, response->total_chunks);
    return NRF_SUCCESS;
}

ret_code_t download_chunk_handler(DownloadChunkRequest *request, DownloadChunkResponse *response)
{
    FRESULT ff_result;
    UINT bytes_read;
    uint32_t expected_position;

    if (!download_active) {
        NRF_LOG_ERROR("No active download session");
        response->chunk_size = 0;
        return NRF_SUCCESS;
    }

    expected_position = request->chunk_index * DOWNLOAD_CHUNK_SIZE;

    if (current_position != expected_position) {
        ff_result = f_lseek(&download_file, expected_position);
        if (ff_result != FR_OK) {
            NRF_LOG_ERROR("Failed to seek to position %u in file %s: %d", expected_position, current_filename, ff_result);
            response->chunk_size = 0;
            return NRF_SUCCESS;
        }
        current_position = expected_position;
    }

    ff_result = f_read(&download_file, response->data, DOWNLOAD_CHUNK_SIZE, &bytes_read);
    if (ff_result != FR_OK) {
        NRF_LOG_ERROR("Failed to read chunk from file %s: %d", current_filename, ff_result);
        response->chunk_size = 0;
        return NRF_SUCCESS;
    }

    response->chunk_index = request->chunk_index;
    response->chunk_size = bytes_read;
    response->is_last_chunk = (current_position + bytes_read >= current_file_size) ? 1 : 0;
    current_position += bytes_read;

    if (response->is_last_chunk) {
        f_close(&download_file);
        download_active = false;
        NRF_LOG_INFO("Download completed for file: %s", current_filename);
    }

    return NRF_SUCCESS;
}

ret_code_t get_file_checksum_handler(GetFileChecksumRequest *request, GetFileChecksumResponse *response)
{
    FIL file;
    FRESULT ff_result;
    uint8_t buffer[256];
    UINT bytes_read;
    uint32_t crc = 0;

    ff_result = f_open(&file, request->filename, FA_READ);
    if (ff_result != FR_OK) {
        NRF_LOG_ERROR("Failed to open file for checksum: %s, error: %d", request->filename, ff_result);
        response->success = 0;
        return NRF_SUCCESS;
    }

    do {
        ff_result = f_read(&file, buffer, sizeof(buffer), &bytes_read);
        if (ff_result == FR_OK && bytes_read > 0) {
            crc = calculate_crc32(buffer, bytes_read);
        }
    } while (ff_result == FR_OK && bytes_read > 0);

    f_close(&file);

    response->checksum = crc;
    response->success = (ff_result == FR_OK) ? 1 : 0;

    return NRF_SUCCESS;
}


static uint32_t calculate_crc32(const uint8_t *data, size_t length)
{
    uint32_t crc = 0xFFFFFFFF;
    for (size_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++) {
            if (crc & 1) {
                crc = (crc >> 1) ^ 0xEDB88320;
            } else {
                crc >>= 1;
            }
        }
    }
    return ~crc;
}