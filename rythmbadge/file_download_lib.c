#include "file_download_lib.h"
#include "ff.h"
#include "nrf_log.h"
#include <string.h>

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

    do {
        ff_result = f_readdir(&dir, &fno);
        if (ff_result == FR_OK && fno.fname[0]) {
            if (!(fno.fattrib & AM_DIR))  // Only process files, not directories
                total_files++;
        }
    } while (ff_result == FR_OK && fno.fname[0]);
    f_closedir(&dir);

    ff_result = f_opendir(&dir, "/");
    if (ff_result != FR_OK) {
        NRF_LOG_ERROR("Failed to open root directory again: %d", ff_result);
        return NRF_ERROR_NOT_FOUND;
    }

    memset(response, 0, sizeof(ListFilesResponse));
    response->header.total_files = total_files;
    response->header.start_index = request->start_index;

    do {
        ff_result = f_readdir(&dir, &fno);
        if (ff_result == FR_OK && fno.fname[0]) {
            if (!(fno.fattrib & AM_DIR)) { 
                if (current_index >= request->start_index && file_index < request->max_files && file_index < 3) {
                    strncpy(response->files[file_index].filename, fno.fname, MAX_FILENAME_LENGTH - 1);
                    response->files[file_index].file_size = fno.fsize;
                    response->files[file_index].timestamp = fno.fdate;
                    file_index++;
            }
            current_index++;
            }
        }
    } while (ff_result == FR_OK && fno.fname[0] && file_index < 3);

    response->header.file_count = file_index;
    f_closedir(&dir);

    return NRF_SUCCESS;
}
