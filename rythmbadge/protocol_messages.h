#ifndef __PROTOCOL_MESSAGES_02V1_H
#define __PROTOCOL_MESSAGES_02V1_H

#include <stdint.h>

#define Request_status_request_tag 1
#define Request_start_microphone_request_tag 2
#define Request_stop_microphone_request_tag 3
#define Request_start_scan_request_tag 4
#define Request_stop_scan_request_tag 5
#define Request_start_imu_request_tag 6
#define Request_stop_imu_request_tag 7
#define Request_identify_request_tag 27
#define Request_restart_request_tag 29
#define Request_free_sdc_space_request_tag 30
#define Request_sdc_errase_all_request_tag 31
#define Request_get_imu_data_request_tag 33
#define Request_get_fw_version_request_tag 35

#define Response_status_response_tag 1
#define Response_start_microphone_response_tag 2
#define Response_start_scan_response_tag 3
#define Response_start_imu_response_tag 4
#define Response_free_sdc_space_response_tag 5
#define Response_sdc_errase_all_response_tag 32
#define Response_get_imu_data_response_tag 34
#define Response_get_fw_version_response_tag 36

typedef struct __attribute__((__packed__)) {
	uint32_t seconds;
	uint16_t ms;
} Timestamp;

typedef struct __attribute__((__packed__)) {
	uint16_t ID;
	uint8_t group;
} BadgeAssignment;

typedef struct {
	Timestamp timestamp;
	uint8_t has_badge_assignement;
	BadgeAssignment badge_assignement;
} StatusRequest;

typedef struct {
	Timestamp timestamp;
	uint8_t mode;
} StartMicrophoneRequest;

typedef struct {
} StopMicrophoneRequest;

typedef struct __attribute__((__packed__)) {
	Timestamp timestamp;
	uint16_t window;
	uint16_t interval;
} StartScanRequest;

typedef struct {
} StopScanRequest;

typedef struct __attribute__((__packed__)) {
	Timestamp timestamp;
	uint16_t acc_fsr;
	uint16_t gyr_fsr;
	uint16_t datarate;
} StartImuRequest;

typedef struct {
} StopImuRequest;

typedef struct {
	uint16_t timeout;
} IdentifyRequest;

typedef struct {
} RestartRequest;

typedef struct {
} FreeSDCSpaceRequest;

typedef struct {
} ErraseAllRequest;

typedef struct {
} GetIMUDataRequest;

typedef struct{
} GetFWVersionRequest; 


typedef struct __attribute__((__packed__)) {
	uint8_t which_type;
	union {
		StatusRequest status_request;
		StartMicrophoneRequest start_microphone_request;
		StopMicrophoneRequest stop_microphone_request;
		StartScanRequest start_scan_request;
		StopScanRequest stop_scan_request;
		StartImuRequest start_imu_request;
		StopImuRequest stop_imu_request;
		IdentifyRequest identify_request;
		RestartRequest restart_request;
		FreeSDCSpaceRequest free_sdc_space_request;
		ErraseAllRequest sdc_errase_all_request;
		GetIMUDataRequest get_imu_data_request;
		GetFWVersionRequest get_fw_version_request;
	} type;
} Request;

typedef struct {
	uint8_t clock_status;
	uint8_t microphone_status;
	uint8_t scan_status;
	uint8_t imu_status;
	int8_t battery_level;
	uint32_t pdm_data;
	uint16_t scan_data;
	int32_t time_delta;
	Timestamp timestamp;
} StatusResponse;

typedef struct {
	Timestamp timestamp;
	uint8_t mode;
	int8_t gain_l;
	int8_t gain_r;
	int8_t switch_pos; //0: OFF, 1: LOW, 2: HIGH
	uint16_t pdm_freq; // KHz
} StartMicrophoneResponse;

typedef struct {
	Timestamp timestamp;
	uint16_t window;
	uint16_t interval;
} StartScanResponse;

typedef struct {
	Timestamp timestamp;
	uint8_t self_test_done;
	uint32_t gyr_fsr;
	uint32_t acc_fsr;
	uint8_t datarate;
} StartImuResponse;

typedef struct {
	uint32_t total_space;
	uint32_t free_space;
	Timestamp timestamp;
} FreeSDCSpaceResponse;

typedef struct {
	uint8_t done_errase;
	Timestamp timestamp;
} ErraseAllResponse;

typedef struct {
	uint16_t gyr_x;
	uint16_t gyr_y;
	uint16_t gyr_z;
	uint16_t mag_x;
	uint16_t mag_y;
	uint16_t mag_z;
	uint16_t acc_x;
	uint16_t acc_y;
	uint16_t acc_z;
	uint16_t rot_x;
	uint16_t rot_y;
	uint16_t rot_z;
	Timestamp timestamp;
} GetIMUDataResponse;

#define VERSION_STR_SZ 32
typedef struct{
	char version[VERSION_STR_SZ];
} GetFWVersionResponse; 

//typedef struct __attribute__((__packed__)) {
typedef struct {
	uint8_t which_type;
	union {
		StatusResponse status_response;
		StartMicrophoneResponse start_microphone_response;
		StartScanResponse start_scan_response;
		StartImuResponse start_imu_response;
		FreeSDCSpaceResponse free_sdc_space_response;
		ErraseAllResponse sdc_errase_all_response;
		GetIMUDataResponse get_imu_data_response;
		GetFWVersionResponse get_fw_version_response;
	} type;
} Response;


#endif
