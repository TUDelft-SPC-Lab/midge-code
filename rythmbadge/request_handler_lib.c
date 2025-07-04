#include "request_handler_lib.h"
#include "audio_switch.h"
#include <protocol_messages.h>
#include <string.h>
#include "app_fifo.h"
#include "drv_audio_pdm.h"
#include "app_scheduler.h"
#include "sender_lib.h"
#include "systick_lib.h"
#include "sampling_lib.h"
#include "advertiser_lib.h"	// To retrieve the current badge-assignement and set the clock-sync status
#include "storage.h" // getfreespace
#include "nrf_gpio.h"
#include "saadc.h"
#include "ICM20948_driver_interface.h"
#include "nrf_log.h"
#include "boards.h"
#include "ble_lib.h"
#include "file_download_lib.h"

#define RECEIVE_NOTIFICATION_FIFO_SIZE					256		/**< Buffer size for the receive-notification FIFO. Has to be a power of two */
#define AWAIT_DATA_TIMEOUT_MS							1000
#define TRANSMIT_DATA_TIMEOUT_MS						100
#define REQUEST_HANDLER_BUFFER_SIZE			512
#define RESPONSE_MAX_TRANSMIT_RETRIES					50		


typedef struct {
	uint64_t 	request_timepoint_ticks;
	Request 	request;
} request_event_t;

typedef struct {
	uint32_t					response_retries;
	app_sched_event_handler_t	response_fail_handler;		/**< Scheduler function that should be called, if the response could not be transmitted */
	Response					response;
} response_event_t;

typedef void (* request_handler_t)(void * p_event_data, uint16_t event_size);

typedef struct {
    uint8_t type;
    request_handler_t handler;
} request_handler_for_type_t;


static request_event_t  request_event;	/**< Needed a reponse event, to put the timepoint ticks into the structure */
static response_event_t	response_event; /**< Needed a reponse event, to put the reties and the function to call after success into the structure */
static Timestamp		response_timestamp; /**< Needed for the status-, and start-requests */
static uint8_t			response_clock_status;	/**< Needed for the status-, and start-requests */

static app_fifo_t receive_notification_fifo;
static uint8_t receive_notification_buf[RECEIVE_NOTIFICATION_FIFO_SIZE];
static volatile uint8_t processing_receive_notification = 0;			/**< Flag that represents if the processing of a receive notification is still running. */
static volatile uint8_t processing_response = 0;						/**< Flag that represents if the processing of response is still running. */

static uint8_t notserialized_buf[REQUEST_HANDLER_BUFFER_SIZE];

static void receive_notification_handler(receive_notification_t receive_notification);
static void process_receive_notification(void * p_event_data, uint16_t event_size);


static void status_request_handler(void * p_event_data, uint16_t event_size);
static void start_microphone_request_handler(void * p_event_data, uint16_t event_size);
static void stop_microphone_request_handler(void * p_event_data, uint16_t event_size);
static void start_scan_request_handler(void * p_event_data, uint16_t event_size);
static void stop_scan_request_handler(void * p_event_data, uint16_t event_size);
static void start_imu_request_handler(void * p_event_data, uint16_t event_size);
static void stop_imu_request_handler(void * p_event_data, uint16_t event_size);

static void identify_request_handler(void * p_event_data, uint16_t event_size);
static void restart_request_handler(void * p_event_data, uint16_t event_size);
static void free_sdc_space_request_handler(void * p_event_data, uint16_t event_size);
static void sdc_errase_all_request_handler(void * p_event_data, uint16_t event_size);

static void get_imu_data_request_handler(void * p_event_data, uint16_t event_size);
static void get_fw_version_request_handler(void * p_event_data, uint16_t evem_size);
static void list_files_request_handler(void * p_event_data, uint16_t event_size);
static void start_download_request_handler(void * p_event_data, uint16_t event_size);
static void download_chunk_request_handler(void * p_event_data, uint16_t event_size);
static void get_file_checksum_request_handler(void * p_event_data, uint16_t event_size);

static void status_response_handler(void * p_event_data, uint16_t event_size);
static void start_microphone_response_handler(void * p_event_data, uint16_t event_size);
static void start_scan_response_handler(void * p_event_data, uint16_t event_size);
static void start_imu_response_handler(void * p_event_data, uint16_t event_size);
static void free_sdc_space_response_handler(void * p_event_data, uint16_t event_size);
static void sdc_errase_all_response_handler(void * p_event_data, uint16_t event_size);
static void get_imu_data_response_handler(void * p_event_data, uint16_t event_size);
static void list_files_response_handler(void * p_event_data, uint16_t event_size);
static void start_download_response_handler(void * p_event_data, uint16_t event_size);
static void download_chunk_response_handler(void * p_event_data, uint16_t event_size);
static void get_file_checksum_response_handler(void * p_event_data, uint16_t event_size);

static request_handler_for_type_t request_handlers[] = {
        {
                .type = Request_status_request_tag,
                .handler = status_request_handler,
        },
        {
                .type = Request_start_microphone_request_tag,
                .handler = start_microphone_request_handler,
        },
		{
                .type = Request_stop_microphone_request_tag,
                .handler = stop_microphone_request_handler,
        },
        {
                .type = Request_start_scan_request_tag,
                .handler = start_scan_request_handler,
        },
        {
                .type = Request_stop_scan_request_tag,
                .handler = stop_scan_request_handler,
        },
		{
                .type = Request_start_imu_request_tag,
                .handler = start_imu_request_handler,
        },
        {
                .type = Request_stop_imu_request_tag,
                .handler = stop_imu_request_handler,
        },
		{
                .type = Request_identify_request_tag,
                .handler = identify_request_handler,
        },
		{
                .type = Request_restart_request_tag,
                .handler = restart_request_handler,
        },
		{
                .type = Request_free_sdc_space_request_tag,
                .handler = free_sdc_space_request_handler,
        },
		{
                .type = Request_sdc_errase_all_request_tag,
                .handler = sdc_errase_all_request_handler,
        },
		{
                .type = Request_get_imu_data_request_tag,
                .handler = get_imu_data_request_handler,
        },	
		{
                .type = Request_get_fw_version_request_tag,
                .handler = get_fw_version_request_handler,
        },
		{
				.type = Request_list_files_request_tag,
				.handler = list_files_request_handler,
		},
		{
				.type = Request_start_download_request_tag,
				.handler = start_download_request_handler,
		},
		{
				.type = Request_download_chunk_request_tag,
				.handler = download_chunk_request_handler,
		},
		{
				.type = Request_get_file_checksum_request_tag,
				.handler = get_file_checksum_request_handler,
		}
};



ret_code_t request_handler_init(void)
{
	ret_code_t ret = sender_init();
	if(ret != NRF_SUCCESS) return ret;
	
	sender_set_receive_notification_handler(receive_notification_handler);
	
	ret = app_fifo_init(&receive_notification_fifo, receive_notification_buf, sizeof(receive_notification_buf));
	if(ret != NRF_SUCCESS) return ret;
	
	return NRF_SUCCESS;
}

/**@brief Handler that is called  by the sender-module, when a notification was received.
 * 
 * @details It puts the received notification in the notification-fifo and schedules the process_receive_notification to process the notification.
 */
static void receive_notification_handler(receive_notification_t receive_notification)
{
	// Put the receive_notification into the fifo
	uint32_t available_len = 0;
	uint32_t notification_size = sizeof(receive_notification);
	app_fifo_write(&receive_notification_fifo, NULL, &available_len);
	if(available_len < notification_size) {
		NRF_LOG_INFO("REQUEST_HANDLER: Not enough bytes in Notification FIFO: %u < %u\n", available_len, notification_size);
		return;
	}
	
	app_fifo_write(&receive_notification_fifo, (uint8_t*) &receive_notification, &notification_size);
	
	app_sched_event_put(NULL, 0, process_receive_notification);

}

static void finish_receive_notification(void)
{
	processing_receive_notification = 0;
}

static void finish_and_reschedule_receive_notification(void)
{
	processing_receive_notification = 0;
	app_sched_event_put(NULL, 0, process_receive_notification);
}

static ret_code_t start_receive_notification(app_sched_event_handler_t reschedule_handler)
{
	if(processing_receive_notification)
	{
		app_sched_event_put(NULL, 0, reschedule_handler);
		return NRF_ERROR_BUSY;
	}
	processing_receive_notification = 1;
	return NRF_SUCCESS;
}


static ret_code_t start_response(app_sched_event_handler_t reschedule_handler)
{
	if(processing_response)
	{	// Check if we are allowed to prepare and send our response, if not reschedule the response-handler again
		app_sched_event_put(NULL, 0, reschedule_handler);
		return NRF_ERROR_BUSY;
	}
	processing_response = 1;
	return NRF_SUCCESS;
}


// Called when await data failed, or decoding the notification failed, or request does not exist, or transmitting the response failed (because disconnected or something else)
static void finish_error(void)
{
	app_fifo_flush(&receive_notification_fifo);
	NRF_LOG_INFO("REQUEST_HANDLER: Error while processing request/response --> Disconnect!!!\n");
	sender_disconnect();	// To clear the RX- and TX-FIFO
	finish_receive_notification();
	processing_response = 0;
}


static ret_code_t receive_notification_fifo_peek(receive_notification_t* receive_notification, uint32_t index)
{
	uint32_t notification_size = sizeof(receive_notification_t);
	uint32_t available_size;
	app_fifo_read(&receive_notification_fifo, NULL, &available_size);
	if(available_size < notification_size*(index+1)) {
		return NRF_ERROR_NOT_FOUND;
	}
	
	uint8_t tmp[notification_size];
	memset(tmp, 0, sizeof(tmp));
	for(uint32_t i = 0; i < notification_size; i++) {
		app_fifo_peek(&receive_notification_fifo, i + index*notification_size, &(tmp[i]));
	}
	
	memcpy(receive_notification, tmp, notification_size);
	return NRF_SUCCESS;
}

static void receive_notification_fifo_consume(void)
{
	uint32_t notification_size = sizeof(receive_notification_t);
	uint8_t tmp[notification_size];
	app_fifo_read(&receive_notification_fifo, tmp, &notification_size);
}

static void receive_notification_fifo_set_receive_notification(receive_notification_t* receive_notification, uint32_t index)
{
	uint32_t notification_size = sizeof(receive_notification_t);
	uint32_t available_size;
	app_fifo_read(&receive_notification_fifo, NULL, &available_size);
	if(available_size < notification_size*(index+1)) {
		return;
	}
	uint8_t tmp[notification_size];
	memcpy(tmp, receive_notification, notification_size);
	// Manually set the bytes of the notification in the FIFO
	uint32_t start_index = receive_notification_fifo.read_pos + index*notification_size;
	for(uint32_t i = 0; i < notification_size; i++) {
		receive_notification_fifo.p_buf[(start_index + i) & receive_notification_fifo.buf_size_mask] = tmp[i];
	}	
}

/**
 * This function could handle multiple queued receive notifications.
 * It searches for the length of the packet and then splits the 
 * queued receive notifications that belongs to the actual whole packet
 * and removes the receive notificatins from the queue.
 *
 * Then it calls the corresponding request handler.
 * If the request-handler is done, it finishes the processing of the receive notification, 
 * and reschedules the processing of new receive notifications.
 */
static void process_receive_notification(void * p_event_data, uint16_t event_size)
{
	// Check if we can start the processing of the receive notification, otherwise reschedule
	if(start_receive_notification(process_receive_notification) != NRF_SUCCESS)
		return;

	// Get the first receive-notification in the FIFO. If there is no in the queue --> we are finish with processing receive notifications.
	receive_notification_t receive_notification;
	ret_code_t ret = receive_notification_fifo_peek(&receive_notification, 0);
	if(ret == NRF_ERROR_NOT_FOUND) {
		app_fifo_flush(&receive_notification_fifo);
		finish_receive_notification();
		return;
	}
	
	// Get the timestamp and clock-sync status before processing the request!
	response_timestamp.seconds = receive_notification.timepoint_seconds;
	response_timestamp.ms = receive_notification.timepoint_milliseconds;
	response_clock_status = systick_is_synced();
	
	uint64_t timepoint_ticks = receive_notification.timepoint_ticks;
	
	// Wait for the length header bytes
	uint8_t length_header[2];
	ret = sender_await_data(length_header, 2, AWAIT_DATA_TIMEOUT_MS);
	if(ret != NRF_SUCCESS) {
		NRF_LOG_INFO("REQUEST_HANDLER: sender_await_data() error for length header\n");
		app_fifo_flush(&receive_notification_fifo);
		finish_error();
		return;
	}
	
	uint16_t len = (((uint16_t)length_header[1]) << 8) | ((uint16_t)length_header[0]);
	
	// Now wait for the actual data
	ret = sender_await_data(notserialized_buf, len, AWAIT_DATA_TIMEOUT_MS);
	if(ret != NRF_SUCCESS) {
		NRF_LOG_INFO("REQUEST_HANDLER: sender_await_data() error\n");
		app_fifo_flush(&receive_notification_fifo);
		finish_error();
		return;
	}
	
	// Here we assume that we got enough receive notifications to receive all the data,
	// so we need to consume all notifications in the notification-fifo that corresponds to this data
	uint16_t consume_len = len + 2;	// + 2 for the header
	uint32_t consume_index = 0;
	while(consume_len > 0)
	{
		ret = receive_notification_fifo_peek(&receive_notification, consume_index);
		if(ret == NRF_ERROR_NOT_FOUND)
		{
			app_fifo_flush(&receive_notification_fifo);
			finish_error();
			return;
		}
		if(receive_notification.notification_len <= consume_len)
		{
			consume_len -= receive_notification.notification_len;
			// Increment the consume_index here, to consume the right number of notifications in the end
			consume_index++;
		} else {			
			// Adapt the notification-len of the consume_index-th notification
			receive_notification.notification_len = receive_notification.notification_len - consume_len;
			NRF_LOG_INFO("REQUEST_HANDLER: Adapt %u. notification len to %u\n", consume_index, receive_notification.notification_len);
			receive_notification_fifo_set_receive_notification(&receive_notification, consume_index);
			// Set consume len to 0
			consume_len = 0;
		}
	}
	NRF_LOG_INFO("REQUEST_HANDLER: Consume %u notifications\n", consume_index);
	
	// Now manually consume the notifications
	for(uint32_t i = 0; i < consume_index; i++) {
		receive_notification_fifo_consume();
	}
	
	
	memcpy(&(request_event.request), notserialized_buf, sizeof(request_event.request));


	request_event.request_timepoint_ticks = timepoint_ticks;

	
	NRF_LOG_INFO("REQUEST_HANDLER: Which request type: %u, Ticks: %u\n", request_event.request.which_type, request_event.request_timepoint_ticks);

	request_handler_t request_handler = NULL;
	for(uint8_t i = 0; i < sizeof(request_handlers)/sizeof(request_handler_for_type_t); i++)
	{
		if(request_event.request.which_type == request_handlers[i].type)
		{
			request_handler = request_handlers[i].handler;
			break;
		}
		
	}
	if(request_handler != NULL)
	{
		// These request-handlers finish the processing of the receive notification
		request_handler(NULL, 0);
	} else {
		// Should actually not happen, but to be sure...
		NRF_LOG_INFO("REQUEST_HANDLER: Have not found a corresponding request handler for which_type: %u\n", request_event.request.which_type);
		finish_error();
	}
}


static void send_response(void * p_event_data, uint16_t event_size) {
	// On transmit failure, reschedule itself
	response_event.response_fail_handler = send_response;
	
	// Check if we already had too much retries
	if(response_event.response_retries > RESPONSE_MAX_TRANSMIT_RETRIES) {
		finish_error();
		return;
	}
	
	response_event.response_retries++;
	
	
	uint32_t len = sizeof(response_event.response.type); // no point in this, it is always the size of the largest entry = 16bytes for get free space
	memcpy(&notserialized_buf[2], &(response_event.response), len); //notserialized_buf[2]=response_event.response
	
	ret_code_t ret = NRF_SUCCESS;

	notserialized_buf[1] = (uint8_t)((((uint16_t) len) & 0xFF00) >> 8);
	notserialized_buf[0] = (uint8_t)(((uint16_t) len) & 0xFF);
	ret = sender_transmit(notserialized_buf, len+2, TRANSMIT_DATA_TIMEOUT_MS);
	
	NRF_LOG_INFO("REQUEST_HANDLER: Transmit status %u!\n", ret);

	if(ret == NRF_SUCCESS) {
		
		processing_response = 0;	// We are now done with this reponse
	
	} else {
		if(ret == NRF_ERROR_NO_MEM)	// Only reschedule a fail handler, if we could not transmit because of memory problems
			if(response_event.response_fail_handler != NULL) {	// This function should actually always be set..
				app_sched_event_put(NULL, 0, response_event.response_fail_handler);
				return;
			}
		// Some BLE-problems occured (e.g. disconnected...)
		finish_error();
	}
}


/**
 Every request-handler has an response-handler!
*/





/**< These are the response handlers, that are called by the request-handlers. */

static void status_response_handler(void * p_event_data, uint16_t event_size)
{
	if(start_response(status_response_handler) != NRF_SUCCESS)
		return;

	response_event.response.which_type = Response_status_response_tag;
	response_event.response.type.status_response.clock_status = advertiser_get_status_flag_is_clock_synced();
	response_event.response.type.status_response.microphone_status = advertiser_get_status_flag_microphone_enabled();
	response_event.response.type.status_response.scan_status = advertiser_get_status_flag_scan_enabled();
	response_event.response.type.status_response.imu_status = advertiser_get_status_flag_imu_enabled();
	response_event.response.type.status_response.battery_level = get_battery_level();
	response_event.response.type.status_response.pdm_data = pdm_buf[0].mic_buf[0];
	response_event.response.type.status_response.scan_data = ble_get_scan_rssi();
	response_event.response.type.status_response.timestamp = response_timestamp;

	response_event.response_retries = 0;
	
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification. 
	send_response(NULL, 0);	

}

static void start_microphone_response_handler(void * p_event_data, uint16_t event_size)
{
	if(start_response(start_microphone_response_handler) != NRF_SUCCESS)
		return;
	
	response_event.response.which_type = Response_start_microphone_response_tag;
	response_event.response_retries = 0;
	response_event.response.type.start_microphone_response.timestamp = response_timestamp;
	response_event.response.type.start_microphone_response.mode = drv_audio_get_mode();
	response_event.response.type.start_microphone_response.switch_pos = audio_switch_get_position();
	response_event.response.type.start_microphone_response.gain_l = drv_audio_get_gain_l();
	response_event.response.type.start_microphone_response.gain_r = drv_audio_get_gain_r();
	response_event.response.type.start_microphone_response.pdm_freq = drv_audio_get_pdm_freq();

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification. 
	send_response(NULL, 0);	
}


static void start_scan_response_handler(void * p_event_data, uint16_t event_size)
{
	if(start_response(start_scan_response_handler) != NRF_SUCCESS)
		return;
	
	response_event.response.which_type = Response_start_scan_response_tag;
	response_event.response_retries = 0;
	response_event.response.type.start_scan_response.timestamp = response_timestamp;
	response_event.response.type.start_scan_response.window = ble_get_scan_window();
	response_event.response.type.start_scan_response.interval = ble_get_scan_interval();
	
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification. 
	send_response(NULL, 0);	
}

static void start_imu_response_handler(void * p_event_data, uint16_t event_size) {
	if(start_response(start_imu_response_handler) != NRF_SUCCESS)
		return;
	
	response_event.response.which_type = Response_start_imu_response_tag;
	response_event.response_retries = 0;
	response_event.response.type.start_imu_response.timestamp = response_timestamp;
	response_event.response.type.start_imu_response.self_test_done = inv_icm20948_get_self_test_done(); 
	response_event.response.type.start_imu_response.gyr_fsr = get_gyr_fsr();
	response_event.response.type.start_imu_response.acc_fsr = get_acc_fsr();
	response_event.response.type.start_imu_response.datarate = get_datarate();
	
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification. 
	send_response(NULL, 0);	
}

static void free_sdc_space_response_handler(void * p_event_data, uint16_t event_size)
{
	response_event.response.which_type = Response_free_sdc_space_response_tag;
	response_event.response_retries = 0;
	if (sampling_get_sampling_configuration() == 0) //if sd card is writing, we will drop samples
		storage_get_free_space(&response_event.response.type.free_sdc_space_response.total_space, &response_event.response.type.free_sdc_space_response.free_space);
	response_event.response.type.free_sdc_space_response.timestamp = response_timestamp;

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification.
	send_response(NULL, 0);
}

static void sdc_errase_all_response_handler(void * p_event_data, uint16_t event_size)
{
	response_event.response.which_type = Response_sdc_errase_all_response_tag;
	response_event.response_retries = 0;
	response_event.response.type.sdc_errase_all_response.done_errase = 0;
	if (sampling_get_sampling_configuration() == 0) //if sd card is writing, we will drop samples
		response_event.response.type.sdc_errase_all_response.done_errase = sdc_errase_all();
	response_event.response.type.sdc_errase_all_response.timestamp = response_timestamp;

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification.
	send_response(NULL, 0);
}

static void get_imu_data_response_handler(void * p_event_data, uint16_t event_size)
{
	response_event.response.which_type = Response_get_imu_data_response_tag;
	response_event.response_retries = 0;

	if (advertiser_get_status_flag_imu_enabled() == 1)
	{ //if sd card is writing, we will drop samples
		response_event.response.type.get_imu_data_response.gyr_x = get_gyr_x();
		response_event.response.type.get_imu_data_response.gyr_y = get_gyr_y();
		response_event.response.type.get_imu_data_response.gyr_z = get_gyr_z();

		response_event.response.type.get_imu_data_response.mag_x = get_mag_x();
		response_event.response.type.get_imu_data_response.mag_y = get_mag_y();
		response_event.response.type.get_imu_data_response.mag_z = get_mag_z();

		response_event.response.type.get_imu_data_response.acc_x = get_acc_x();
		response_event.response.type.get_imu_data_response.acc_y = get_acc_y();
		response_event.response.type.get_imu_data_response.acc_z = get_acc_z();

		response_event.response.type.get_imu_data_response.rot_x = get_rot_x();
		response_event.response.type.get_imu_data_response.rot_y = get_rot_y();
		response_event.response.type.get_imu_data_response.rot_z = get_rot_z();
	}
	else { //if sd card is writing, we will drop samples
		response_event.response.type.get_imu_data_response.gyr_x = 0;
		response_event.response.type.get_imu_data_response.gyr_y = 0;
		response_event.response.type.get_imu_data_response.gyr_z = 0;

		response_event.response.type.get_imu_data_response.mag_x = 0;
		response_event.response.type.get_imu_data_response.mag_y = 0;
		response_event.response.type.get_imu_data_response.mag_z = 0;

		response_event.response.type.get_imu_data_response.acc_x = 0;
		response_event.response.type.get_imu_data_response.acc_y = 0;
		response_event.response.type.get_imu_data_response.acc_z = 0;

		response_event.response.type.get_imu_data_response.rot_x = 0;
		response_event.response.type.get_imu_data_response.rot_y = 0;
		response_event.response.type.get_imu_data_response.rot_z = 0;
	
	}
	response_event.response.type.get_imu_data_response.timestamp = response_timestamp;

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification.
	send_response(NULL, 0);
}

#ifndef VERSION
#error "VERSION VALUE NOT PROVIDED"
#endif
static void get_fw_version_response_handler(void * p_event_data, uint16_t event_size)
{
	if(start_response(get_fw_version_response_handler) != NRF_SUCCESS)
		return;

	response_event.response.which_type = Response_get_fw_version_response_tag;
	char* v = VERSION;
	memset(response_event.response.type.get_fw_version_response.version, 
		0, VERSION_STR_SZ);
	strcpy(response_event.response.type.get_fw_version_response.version, v);
	response_event.response_retries = 0;
	
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification. 
	send_response(NULL, 0);	
}


static void list_files_response_handler(void * p_event_data, uint16_t event_size)
{
	if (start_response(list_files_response_handler) != NRF_SUCCESS)
		return;

	response_event.response.which_type = Response_list_files_response_tag;
	response_event.response_retries = 0;

	ListFilesRequest list_request = {
		.start_index = request_event.request.type.list_files_request.start_index,
		.max_files = request_event.request.type.list_files_request.max_files,
	};

	ret_code_t ret = list_files_handler(&list_request, &response_event.response.type.list_files_response);

	if (ret != NRF_SUCCESS) {
		NRF_LOG_WARNING("REQUEST_HANDLER: Error while listing files: %d\n", ret);
		memset(&response_event.response.type.list_files_response, 0, sizeof(response_event.response.type.list_files_response));
	}

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification.
	send_response(NULL, 0);
}

static void start_download_response_handler(void * p_event_data, uint16_t event_size)
{
	if (start_response(start_download_response_handler) != NRF_SUCCESS)
		return;

	response_event.response.which_type = Response_start_download_response_tag;
	response_event.response_retries = 0;

	StartDownloadRequest download_request; 
	strncpy(download_request.filename, 
			request_event.request.type.start_download_request.filename, MAX_FILENAME_LENGTH);
	download_request.filename[MAX_FILENAME_LENGTH - 1] = '\0'; // Ensure null-termination
	
	ret_code_t ret = start_download_handler(&download_request, &response_event.response.type.start_download_response);

	if (ret != NRF_SUCCESS) {
		response_event.response.type.start_download_response.success = 0;
		NRF_LOG_WARNING("REQUEST_HANDLER: Error while starting download: %d\n", ret);
	}

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification.
	send_response(NULL, 0);
}

static void download_chunk_response_handler(void * p_event_data, uint16_t event_size)
{
	if (start_response(download_chunk_response_handler) != NRF_SUCCESS)
		return;

	response_event.response.which_type = Response_download_chunk_response_tag;
	response_event.response_retries = 0;

	DownloadChunkRequest chunk_request = {
		.chunk_index = request_event.request.type.download_chunk_request.chunk_index,
	};

	ret_code_t ret = download_chunk_handler(&chunk_request, &response_event.response.type.download_chunk_response);

	if (ret != NRF_SUCCESS) {
		response_event.response.type.download_chunk_response.chunk_size = 0;
		NRF_LOG_WARNING("REQUEST_HANDLER: Error while downloading chunk: %d\n", ret);
	}

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification.
	send_response(NULL, 0);
}

static void get_file_checksum_response_handler(void * p_event_data, uint16_t event_size)
{
	if (start_response(get_file_checksum_response_handler) != NRF_SUCCESS)
		return;

	response_event.response.which_type = Response_get_file_checksum_response_tag;
	response_event.response_retries = 0;

	GetFileChecksumRequest checksum_request; 
	strncpy(checksum_request.filename, 
			request_event.request.type.get_file_checksum_request.filename, MAX_FILENAME_LENGTH);
	checksum_request.filename[MAX_FILENAME_LENGTH - 1] = '\0'; // Ensure null-termination
	
	ret_code_t ret = get_file_checksum_handler(&checksum_request, &response_event.response.type.get_file_checksum_response);

	if (ret != NRF_SUCCESS) {
		response_event.response.type.get_file_checksum_response.success = 0;
		NRF_LOG_WARNING("REQUEST_HANDLER: Error while getting file checksum: %d\n", ret);
	}

	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification.
	send_response(NULL, 0);
}

/**< These are the request handlers that actually call the response-handlers via the scheduler */

static void status_request_handler(void * p_event_data, uint16_t event_size) {

	// Set the timestamp:
	Timestamp timestamp = request_event.request.type.status_request.timestamp;
	systick_set_timestamp(request_event.request_timepoint_ticks, timestamp.seconds, timestamp.ms);
	advertiser_set_status_flag_is_clock_synced(1);
	
	if(request_event.request.type.status_request.has_badge_assignement) {		
		
		BadgeAssignment badge_assignement;
		badge_assignement = request_event.request.type.status_request.badge_assignement;
		
		advertiser_set_badge_assignement(badge_assignement);
	}
	int32_t error_millis = systick_set_timestamp(request_event.request_timepoint_ticks, timestamp.seconds, timestamp.ms);
	advertiser_set_status_flag_is_clock_synced(1);
	
	app_sched_event_put(&error_millis, sizeof(error_millis), status_response_handler);
}


static void start_microphone_request_handler(void * p_event_data, uint16_t event_size)
{
	// Set the timestamp:
	Timestamp timestamp = request_event.request.type.start_microphone_request.timestamp;
	uint8_t mode = request_event.request.type.start_microphone_request.mode;
	systick_set_timestamp(request_event.request_timepoint_ticks, timestamp.seconds, timestamp.ms);
	advertiser_set_status_flag_is_clock_synced(1);
	
	NRF_LOG_INFO("REQUEST_HANDLER: Start microphone, mode: %d", mode);

	ret_code_t ret = sampling_start_microphone(mode);

	if(ret == NRF_SUCCESS) {
		app_sched_event_put(NULL, 0, start_microphone_response_handler);
	} else {
		app_sched_event_put(NULL, 0, restart_request_handler);
	}
}

static void stop_microphone_request_handler(void * p_event_data, uint16_t event_size)
{
	sampling_stop_microphone();
	NRF_LOG_INFO("REQUEST_HANDLER: Stop microphone");
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification
}

static void start_scan_request_handler(void * p_event_data, uint16_t event_size)
{
	// Set the timestamp:
	Timestamp timestamp = (request_event.request).type.start_scan_request.timestamp;
	systick_set_timestamp(request_event.request_timepoint_ticks, timestamp.seconds, timestamp.ms);
	advertiser_set_status_flag_is_clock_synced(1);
	
	uint16_t window	 	= (request_event.request).type.start_scan_request.window;
	uint16_t interval 	= (request_event.request).type.start_scan_request.interval;
	
	NRF_LOG_INFO("REQUEST_HANDLER: Start scanning with window: %u, interval: %u\n", window, interval);

	ret_code_t ret = sampling_start_scan(interval, window);
	NRF_LOG_INFO("REQUEST_HANDLER: Ret sampling_start_scan: %d\n\r", ret);

	if(ret == NRF_SUCCESS) {
		app_sched_event_put(NULL, 0, start_scan_response_handler);
	} else {
		app_sched_event_put(NULL, 0, restart_request_handler);
	}
}

static void stop_scan_request_handler(void * p_event_data, uint16_t event_size)
{
	sampling_stop_scan();
	NRF_LOG_INFO("REQUEST_HANDLER: Stop scan\n");
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification
}

static void start_imu_request_handler(void * p_event_data, uint16_t event_size)
{
	// Set the timestamp:
	Timestamp timestamp = (request_event.request).type.start_imu_request.timestamp;
	systick_set_timestamp(request_event.request_timepoint_ticks, timestamp.seconds, timestamp.ms);
	advertiser_set_status_flag_is_clock_synced(1);
	
	uint16_t acc_fsr  	= (request_event.request).type.start_imu_request.acc_fsr;
	uint16_t gyr_fsr	= (request_event.request).type.start_imu_request.gyr_fsr;
	uint16_t datarate 	= (request_event.request).type.start_imu_request.datarate;
	
	NRF_LOG_INFO("REQUEST_HANDLER: Start imu with acc_fsr: %d, gyr_fsr: %d, datarate: %d", acc_fsr, gyr_fsr, datarate);
	
	ret_code_t ret = sampling_start_imu(acc_fsr, gyr_fsr, datarate);

	if(ret == NRF_SUCCESS) {
		app_sched_event_put(NULL, 0, start_imu_response_handler);
	} else {
		app_sched_event_put(NULL, 0, restart_request_handler);
	}
}

static void stop_imu_request_handler(void * p_event_data, uint16_t event_size)
{
	sampling_stop_imu();
	NRF_LOG_INFO("REQUEST_HANDLER: Stop imu\n");
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification
}


static void identify_request_handler(void * p_event_data, uint16_t event_size)
{
	uint16_t timeout = (request_event.request).type.identify_request.timeout;
	(void) timeout;
	NRF_LOG_INFO("REQUEST_HANDLER: Identify request with timeout: %u\n", timeout);
	#ifndef UNIT_TEST
	nrf_gpio_pin_write(LED, LED_ON);
	systick_delay_millis(timeout*1000);
	nrf_gpio_pin_write(LED, LED_OFF);
	#endif
	
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification
}

static void restart_request_handler(void * p_event_data, uint16_t event_size) {
	NRF_LOG_INFO("REQUEST_HANDLER: Restart request handler\n");
	#ifndef UNIT_TEST
	NVIC_SystemReset();
	#endif
	finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification
}

static void free_sdc_space_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: Free sdc space request handler\n");

	app_sched_event_put(NULL, 0, free_sdc_space_response_handler);
}

static void sdc_errase_all_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: Free sdc space request handler\n");

	app_sched_event_put(NULL, 0, sdc_errase_all_response_handler);
}

static void get_imu_data_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: get_imu_data\n");

	app_sched_event_put(NULL, 0, get_imu_data_response_handler);
}

static void get_fw_version_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: get_fw_version\n");

	app_sched_event_put(NULL, 0, get_fw_version_response_handler);
}

static void list_files_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: list_files\n");

	if (sampling_get_sampling_configuration() != 0) {
	}

	app_sched_event_put(NULL, 0, list_files_response_handler);
}

static void start_download_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: start_download\n");

	if (sampling_get_sampling_configuration() != 0) {
		response_event.response.which_type = Response_start_download_response_tag;
		response_event.response.type.start_download_response.success = 0;
		response_event.response.type.start_download_response.file_size = 0;
		response_event.response.type.start_download_response.total_chunks = 0;
		response_event.response_retries = 0;
		finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification
		send_response(NULL, 0);
		return;
	}

	app_sched_event_put(NULL, 0, start_download_response_handler);
}

static void download_chunk_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: download_chunk\n");

	app_sched_event_put(NULL, 0, download_chunk_response_handler);
}

static void get_file_checksum_request_handler(void * p_event_data, uint16_t event_size)
{
	NRF_LOG_INFO("REQUEST_HANDLER: get_file_checksum\n");

	if (sampling_get_sampling_configuration() != 0) {
		response_event.response.which_type = Response_get_file_checksum_response_tag;
		response_event.response.type.get_file_checksum_response.success = 0;
		response_event.response.type.get_file_checksum_response.checksum = 0;
		response_event.response_retries = 0;
		finish_and_reschedule_receive_notification();	// Now we are done with processing the request --> we can now advance to the next receive-notification
		send_response(NULL, 0);
		return;
	}

	app_sched_event_put(NULL, 0, get_file_checksum_response_handler);
}
