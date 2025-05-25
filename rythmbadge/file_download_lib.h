#ifndef __FILE_DOWNLOAD_LIB_H
#define __FILE_DOWNLOAD_LIB_H

#include "stdint.h"
#include "protocol_messages.h"
#include "sdk_errors.h"

ret_code_t list_files_handler(ListFilesRequest *request, ListFilesResponse *response);
ret_code_t start_download_handler(StartDownloadRequest *request, StartDownloadResponse *response);
ret_code_t download_chunk_handler(DownloadChunkRequest *request, DownloadChunkResponse *response);
ret_code_t get_file_checksum_handler(GetFileChecksumRequest *request, GetFileChecksumResponse *response);


#endif // __FILE_DOWNLOAD_LIB_H