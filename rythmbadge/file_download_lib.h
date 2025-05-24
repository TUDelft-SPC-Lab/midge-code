#ifndef __FILE_DOWNLOAD_LIB_H
#define __FILE_DOWNLOAD_LIB_H

#include "stdint.h"
#include "protocol_messages.h"
#include "sdk_errors.h"

ret_code_t list_files_handler(ListFilesRequest *request, ListFilesResponse *response);


#endif // __FILE_DOWNLOAD_LIB_H