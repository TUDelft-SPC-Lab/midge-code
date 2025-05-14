#include "storage.h"
#include <stdlib.h>
#include "drv_audio_pdm.h"
#include "boards.h"
#include "ff.h"
#include "diskio_blkdev.h"
#include "nrf_block_dev_sdc.h"
#include "nrf_delay.h"
#include "nrf_log.h"
#include "nrf_gpio.h"
#include "ICM20948_driver_interface.h"
#include "systick_lib.h"
#include "scanner_lib.h"
#include "audio_switch.h"
#include "advertiser_lib.h"
#include "app_timer.h"
#include "sampling_lib.h"

#define F_WRITE_TIMEOUT_MS (75) // 8kB takes max 20ms, stereo at 20kHz at HIGH is 102.4ms
#define F_SYNC_PERIOD_MS (1000*60*5) // 5 min periodic flushing to the sd_card

APP_TIMER_DEF(f_write_timeout_timer);
APP_TIMER_DEF(f_sync_timer);

/**
 * @brief  SDC block device definition
 * */
NRF_BLOCK_DEV_SDC_DEFINE(
        m_block_dev_sdc,
        NRF_BLOCK_DEV_SDC_CONFIG(
                SDC_SECTOR_SIZE,
                APP_SDCARD_CONFIG(SDC_MOSI_PIN, SDC_MISO_PIN, SDC_SCK_PIN, SDC_CS_PIN)
         ),
         NFR_BLOCK_DEV_INFO_CONFIG("Nordic", "SDC", "1.00")
);

FATFS fs;
DIR dir;
FILINFO fno;
FIL audio_file_handle;
FIL audio_metadata_file_handle;
FIL imu_file_handle[MAX_IMU_SOURCES];
FIL scanner_file_handle;
extern uint64_t timestamp_buffer[PDM_BUF_NUM];

void sd_write(void * p_event_data, uint16_t event_size)
{
	static data_source_info_t data_source_info;
	data_source_info = *(data_source_info_t *)p_event_data;

	if (data_source_info.data_source == AUDIO && !audio_file_handle.err)
	{
		app_timer_start(f_write_timeout_timer, APP_TIMER_TICKS(F_WRITE_TIMEOUT_MS), &data_source_info.data_source);
		// size is times two, since this function receives number of bytes, not size of pointer
		FRESULT ff_result = f_write(&audio_file_handle, data_source_info.audio_source_info.audio_buffer, data_source_info.audio_source_info.audio_buffer_length, NULL);
		if (ff_result != FR_OK)
		{
			NRF_LOG_INFO("Audio write to sd failed: %d", ff_result);
		}

	if (!audio_metadata_file_handle.err)
	{
		audio_metadata_t audio_metadata_record;
		audio_metadata_record.timestamp = timestamp_buffer[data_source_info.audio_source_info.buffer_index];

		ff_result = f_write(&audio_metadata_file_handle, &audio_metadata_record, sizeof(audio_metadata_t), NULL);
		if (ff_result != FR_OK)
		{
			NRF_LOG_INFO("Audio timestamp write to sd failed: %d", ff_result);
		}
	}


		app_timer_stop(f_write_timeout_timer);
	}
	else if (data_source_info.data_source == IMU && !imu_file_handle[data_source_info.imu_source_info.imu_source].err)
	{
		app_timer_start(f_write_timeout_timer, APP_TIMER_TICKS(F_WRITE_TIMEOUT_MS), &data_source_info.data_source);
		FRESULT ff_result = f_write(&imu_file_handle[data_source_info.imu_source_info.imu_source], data_source_info.imu_source_info.imu_buffer, sizeof(imu_sample_t)*IMU_BUFFER_SIZE, NULL);
		if (ff_result != FR_OK)
			NRF_LOG_INFO("IMU data write to sd failed: %d", ff_result);
		app_timer_stop(f_write_timeout_timer);
	}
	else if (data_source_info.data_source == SCANNER && !scanner_file_handle.err)
	{
		app_timer_start(f_write_timeout_timer, APP_TIMER_TICKS(F_WRITE_TIMEOUT_MS), &data_source_info.data_source);
		FRESULT ff_result = f_write(&scanner_file_handle, scanner_scan_buffer[data_source_info.scanner_buffer_num], sizeof(scanner_scan_report_t)*SCANNER_BUFFER_LENGTH, NULL);
		if (ff_result != FR_OK)
			NRF_LOG_ERROR("Scanner data write to sd failed: %d", ff_result);
		app_timer_stop(f_write_timeout_timer);
	}
}

// In case the low-quality sdcards block for writting, restart the audio file in order to time-stamp it again.
static void f_write_timeout_handler(void* p_context)
{
	data_source_t data_source = *(data_source_t *)p_context;
	NRF_LOG_ERROR("source: %d caused a timeout at: %lu", data_source, systick_get_millis()/1000);
	if (data_source == AUDIO)
	{
		sampling_stop_microphone();
		nrf_delay_ms(200); // delay to fill the buffer and close the files before opening the new ones
		sampling_start_microphone(-1); //mode = -1 to restart with last requested mode
	}

}

static void f_sync_timeout_handler(void* p_context)
{
//	NRF_LOG_INFO("f_sync timer");
	FRESULT ff_result = FR_OK;

	for (uint8_t sensor=0; sensor<MAX_IMU_SOURCES; sensor++)
	{
		if (!imu_file_handle[sensor].err)
			ff_result |= f_sync(&imu_file_handle[sensor]);
	}
	if (!audio_file_handle.err)
		ff_result |= f_sync(&audio_file_handle);
  if (!audio_metadata_file_handle.err)
    ff_result |= f_sync(&audio_metadata_file_handle);
	if (!scanner_file_handle.err)
		ff_result |= f_sync(&scanner_file_handle);

	if (ff_result != FR_OK)
		NRF_LOG_ERROR("f_sync error: %d", ff_result);

}

uint32_t storage_close_file(data_source_t source)
{
	FRESULT ff_result;

	if (source == AUDIO)
	{
		audio_file_handle.err = 1;
		ff_result = f_close(&audio_file_handle);
		if (ff_result)
		{
			NRF_LOG_INFO("close audio file error: %d", ff_result);
			return -1;
		}

	audio_metadata_file_handle.err = 1;
    ff_result = f_close(&audio_metadata_file_handle);
    if (ff_result)
    {
      NRF_LOG_INFO("close audio timestamp file error: %d", ff_result);
      return -1;
    }
	}
	if (source == IMU)
	{
		for (uint8_t sensor=0; sensor<MAX_IMU_SOURCES; sensor++)
		{
			imu_file_handle[sensor].err = 1;
			ff_result = f_close(&imu_file_handle[sensor]);
			if (ff_result)
			{
				NRF_LOG_INFO("close IMU file error: %d", ff_result);
				return -1;
			}
		}
	}
	if (source == SCANNER)
	{
		scanner_file_handle.err = 1;
		ff_result = f_close(&scanner_file_handle);
		if (ff_result)
		{
			NRF_LOG_INFO("close proximity file error: %d", ff_result);
			return -1;
		}
	}
	return 0;
}

void list_directory(void)
{
	FRESULT ff_result;

	NRF_LOG_INFO("\r\n Listing directory: /");
	ff_result = f_opendir(&dir, "/");
	if (ff_result)
	{
		NRF_LOG_INFO("Directory listing failed!");
	}

	do
	{
		ff_result = f_readdir(&dir, &fno);
		if (ff_result != FR_OK)
		{
			NRF_LOG_INFO("Directory read failed: %d", ff_result);
			break;
		}

		if (fno.fname[0])
		{
			if (fno.fattrib & AM_DIR)
			{
				NRF_LOG_RAW_INFO("   <DIR>   %s\n",(uint32_t)fno.fname);
			}
			else
			{
				NRF_LOG_RAW_INFO("%9lu  %s\n", fno.fsize, (uint32_t)fno.fname);
			}
		}
	}
	while (fno.fname[0]);
}

uint8_t sdc_errase_all(void)
{
	FRESULT ff_result;
	DIR dir;
	FILINFO file_info;
	ff_result = f_opendir(&dir, "");
	if (ff_result != FR_OK)
	{		
		NRF_LOG_INFO("f_opendir error");
		return 0;
	}		
	while (1)
	{
		ff_result = f_readdir(&dir, &file_info);
		if (ff_result != FR_OK || file_info.fname[0] == 0)
		{		
			return 1;
		}		

		if (file_info.fattrib & AM_ARC)
		{
			ff_result = f_unlink(file_info.fname);
			if (ff_result == FR_OK)
			{
				NRF_LOG_INFO("File errased: %d", file_info.fname);
			}

			else {
				NRF_LOG_INFO("Error deleting file: %d, name: %s", ff_result, file_info.fname);
				return 0;
			}
			
		}
		
	}
}

uint32_t storage_get_free_space(uint32_t *total_MB, uint32_t *free_MB)
{
	FRESULT ff_result;
    DWORD fre_clust, fre_sect, tot_sect;
    FATFS * p_fs = &fs;

    ff_result = f_getfree("", &fre_clust, &p_fs);
    if (ff_result)
    {
    	NRF_LOG_INFO("get free failed: %d", ff_result);
    	return -1;
    }
    /* Get total sectors and free sectors */
    tot_sect = (p_fs->n_fatent - 2) * p_fs->csize;
    fre_sect = fre_clust * p_fs->csize;

    *total_MB = tot_sect / 2048;
    *free_MB = fre_sect / 2048;

    /* Print the free space (assuming 512 bytes/sector) */
    NRF_LOG_INFO("\n%10lu MiB total drive space.\n%10lu MiB available.\n", tot_sect / 2/1024, fre_sect / 2/1024);

    return NRF_SUCCESS;
}


uint32_t storage_init(void)
{
    FRESULT ff_result;
    DSTATUS disk_state = STA_NOINIT;

    // Initialize FATFS disk I/O interface by providing the block device.
    static diskio_blkdev_t drives[] =
    {
            DISKIO_BLOCKDEV_CONFIG(NRF_BLOCKDEV_BASE_ADDR(m_block_dev_sdc, block_dev), NULL)
    };

    diskio_blockdev_register(drives, ARRAY_SIZE(drives));

    NRF_LOG_INFO("Initializing disk 0 (SDC)...");
    for (uint32_t retries = 3; retries && disk_state; --retries)
    {
        disk_state = disk_initialize(0);
    }
    if (disk_state)
    {
        NRF_LOG_INFO("Disk initialization failed.");
        return 1;
    }

    NRF_LOG_INFO("Mounting volume...");
    ff_result = f_mount(&fs, "", 1);
    if (ff_result)
    {
        NRF_LOG_INFO("Mount failed.");
        return 2;
    }

	// Create the f_write supervisor
	uint32_t ret = app_timer_create(&f_write_timeout_timer, APP_TIMER_MODE_SINGLE_SHOT, f_write_timeout_handler);
	if(ret != NRF_SUCCESS) return NRF_ERROR_INTERNAL;

	// init the error flag so no syncing will occur
	for (uint8_t sensor=0; sensor<MAX_IMU_SOURCES; sensor++)
		imu_file_handle[sensor].err = 1;
	audio_file_handle.err = 1;
	audio_metadata_file_handle.err = 1;
	scanner_file_handle.err = 1;
	// Create the f_sync repeated timer
	ret = app_timer_create(&f_sync_timer, APP_TIMER_MODE_REPEATED, f_sync_timeout_handler);
	if(ret != NRF_SUCCESS) return NRF_ERROR_INTERNAL;
	app_timer_start(f_sync_timer, APP_TIMER_TICKS(F_SYNC_PERIOD_MS), NULL);

    return 0;
}


uint32_t storage_init_folder(uint32_t sync_time_seconds)
{
	NRF_LOG_INFO("open folder");
	FRESULT ff_result;
	BadgeAssignment badge_assignment;
	advertiser_get_badge_assignement(&badge_assignment);
	TCHAR folder[30] = {};

	sprintf(folder, "/%d_%ld", badge_assignment.ID, sync_time_seconds);
	ff_result = f_mkdir(folder);
	if (ff_result)
	{
		NRF_LOG_INFO("Making of new directory failed!");
		return -1;
	}

	ff_result = f_chdir(folder);
	if (ff_result)
	{
		NRF_LOG_INFO("Changing into new directory failed!");
		return -1;
	}

	return 0;
}

int fileCount = 0;

uint32_t storage_open_file(data_source_t source)
{
	FRESULT ff_result;

	uint64_t millis = systick_get_millis();
	uint32_t seconds = millis/1000;
	TCHAR filename[50] = {};
	TCHAR metadata_filename[55] = {};
	NRF_LOG_INFO("SD: seconds: %ld", seconds);
	NRF_LOG_INFO("SD: source: %d", source);
	if (source == AUDIO)
	{

        fileCount = 0;
        while (true)
        {    
            if (audio_switch_get_position()==HIGH) sprintf(filename, "%dMicHi%d", drv_audio_get_mode(), fileCount);
            if (audio_switch_get_position()==LOW) sprintf(filename, "%dMicLo%d", drv_audio_get_mode(), fileCount);
            ff_result = f_stat(filename, &fno);  // Check if the file already exists
            if (ff_result == FR_NO_FILE)
            {
                break;  // File does not exist, break the loop
            }
            if (fileCount >= 99)
            {
                return -1;  // Maximum file count reached
            }
            fileCount++;
        }



		
	    ff_result = f_open(&audio_file_handle, filename, FA_WRITE | FA_CREATE_ALWAYS);
		NRF_LOG_INFO("SD Audio: ff_result: %d", ff_result);
	    if (ff_result != FR_OK)
	    {
	        NRF_LOG_INFO("SD Audio: Unable to open or create file: %d", filename);
	        return -1;
	    }
		audio_file_handle.err = 0;

	sprintf(metadata_filename, "%s.d", filename);
	ff_result = f_open(&audio_metadata_file_handle, metadata_filename, FA_WRITE | FA_CREATE_ALWAYS);
	NRF_LOG_INFO("SD Audio Metadata: ff_result: %d", ff_result);
	if (ff_result != FR_OK)
	{
		NRF_LOG_INFO("SD Audio Metadata: Unable to open or create file: %d", metadata_filename);
		return -1;
	}
	audio_metadata_file_handle.err = 0;
	}
	if (source == IMU)
	{
		for (uint8_t sensor=0; sensor<MAX_IMU_SOURCES; sensor++)
		{
			fileCount = 0;
			while (true)
			{
				sprintf(filename, "%s_%d", imu_sensor_name[sensor], fileCount);
				ff_result = f_stat(filename, &fno);  // Check if the file already exists
				if (ff_result == FR_NO_FILE)
				{
					break;  // File does not exist, break the loop
				}
				if (fileCount >= 99)
				{
					return -1;  // Maximum file count reached
				}
				fileCount++;
			}

		
			ff_result = f_open(&imu_file_handle[sensor], filename, FA_WRITE | FA_CREATE_ALWAYS);
			NRF_LOG_INFO("SD IMU: ff_result: %d", ff_result);
			if (ff_result != FR_OK)
			{
				NRF_LOG_INFO("SD IMU: Unable to open or create file: %d", filename);
				return -1;
			}
			imu_file_handle[sensor].err = 0;
		}
	}
	if (source == SCANNER)
	{
	
		fileCount = 0;
		while (true)
		{
			sprintf(filename, "scan_%d", fileCount);
			ff_result = f_stat(filename, &fno);  // Check if the file already exists
			if (ff_result == FR_NO_FILE)
			{
				break;  // File does not exist, break the loop
			}
			if (fileCount >= 99)
			{
				return -1;  // Maximum file count reached
			}
			fileCount++;
		}
	    ff_result = f_open(&scanner_file_handle, filename, FA_WRITE | FA_CREATE_ALWAYS);
	    NRF_LOG_INFO("SD Scanner: ff_result: %d", ff_result);
		if (ff_result != FR_OK)
	    {
	        NRF_LOG_INFO("SD Scanner: Unable to open or create file: %d", filename);
	        return -1;
	    }
	    scanner_file_handle.err = 0;
	}
	NRF_LOG_INFO("SD: Success creating: %d", filename);

    return 0;
}
