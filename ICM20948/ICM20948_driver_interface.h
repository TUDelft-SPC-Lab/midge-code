#ifndef ICM20948_DRIVER_INTERFACE_H_
#define ICM20948_DRIVER_INTERFACE_H_

#include "Icm20948.h"
#include "storage.h"

#define AK0991x_DEFAULT_I2C_ADDR	0x0C	/* The default I2C address for AK0991x Magnetometers */
#define AK0991x_SECONDARY_I2C_ADDR  0x0E	/* The secondary I2C address for AK0991x Magnetometers */

#define DEF_ST_ACCEL_FS                 2
#define DEF_ST_GYRO_FS_DPS              250
#define DEF_ST_SCALE                    32768
#define DEF_SELFTEST_GYRO_SENS			(DEF_ST_SCALE / DEF_ST_GYRO_FS_DPS)
#define DEF_ST_ACCEL_FS_MG				2000
#define INV20948_ABS(x) (((x) < 0) ? -(x) : (x))


#define IMU_BUFFER_SIZE 64

typedef struct {
	uint64_t timestamp;
	union {
		float axis[3];
		float quat[4];
	};
} imu_sample_t;
// sd_chunk is 24bytes(struct size) * IMU_BUFFER_SIZE, and we want this to be multiple of 512 (sdcard block size)

extern imu_sample_t imu_buffer[MAX_IMU_SOURCES][2][IMU_BUFFER_SIZE];

extern const char *imu_sensor_name[MAX_IMU_SOURCES];


ret_code_t icm20948_init(void);
ret_code_t icm20948_set_fsr(uint32_t acc_fsr, uint32_t gyr_fsr);
ret_code_t icm20948_set_datarate(uint8_t datarate);
ret_code_t icm20948_enable_sensors(void);
ret_code_t icm20948_disable_sensors(void);
void icm20948_service_isr(void * p_event_data, uint16_t event_size);
uint8_t inv_icm20948_get_self_test_done(void);
uint16_t get_acc_x(void);
uint16_t get_acc_y(void);
uint16_t get_acc_z(void);
uint16_t get_mag_x(void);
uint16_t get_mag_y(void);
uint16_t get_mag_z(void);
uint16_t get_gyr_x(void);
uint16_t get_gyr_y(void);
uint16_t get_gyr_z(void);
uint16_t get_rot_x(void);
uint16_t get_rot_y(void);
uint16_t get_rot_z(void);
uint32_t get_acc_fsr(void);
uint32_t get_gyr_fsr(void);
uint8_t get_datarate(void);


#endif /* ICM20948_DRIVER_INTERFACE_H_ */
