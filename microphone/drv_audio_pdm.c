#include <drv_audio_pdm.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <storage.h>

#include "nrf_assert.h"
#include "nrf_error.h"
#include "nrf_gpio.h"
#include "nrf_drv_pdm.h"
#include "nrf_log.h"
#include "ff.h"
#include "app_scheduler.h"
#include "app_timer.h"
#include "SEGGER_RTT.h"
#include "nrf_delay.h"
#include "boards.h"
#include "storage.h"
#include "audio_switch.h"
#include "sampling_lib.h"

ret_code_t err_code;

nrf_drv_pdm_config_t pdm_cfg = NRF_DRV_PDM_DEFAULT_CONFIG(MIC_CLK, MIC_DOUT);
pdm_buf_t pdm_buf[PDM_BUF_NUM];
data_source_info_t data_source_info;
audio_switch_position_t audio_switch_position;
nrf_pdm_mode_t local_mode;
uint32_t local_freq;
uint8_t local_gain_l;
uint8_t local_gain_r;


int16_t subsampled[PDM_BUF_SIZE/DECIMATION];
float filter_weight[DECIMATION];


static void process_audio_buffer(void)
{
	switch (audio_switch_position)
	{
	case OFF:
		break;

	case HIGH:
		if (app_sched_queue_space_get() > 10)
		{
			data_source_info.data_source = AUDIO;
			data_source_info.audio_source_info.audio_buffer_length = PDM_BUF_SIZE*2;
			err_code = app_sched_event_put(&data_source_info, sizeof(data_source_info), sd_write);
			APP_ERROR_CHECK(err_code);
		}
		else
		{
			NRF_LOG_ERROR("dropped audio sample");
			err_code = sampling_stop_microphone();
			err_code |= sampling_start_microphone(-1);
			APP_ERROR_CHECK(err_code);
		}
		break;

	case LOW:
		if (app_sched_queue_space_get() > 10)
		{
			const int16_t * p_sample = data_source_info.audio_source_info.audio_buffer;
			for (uint16_t index=0; index< PDM_BUF_SIZE; index+=(DECIMATION*(pdm_cfg.mode?1:2)))
			{
				memcpy(&subsampled[index/DECIMATION], &p_sample[index], (pdm_cfg.mode?1:2)*2);
			}

			data_source_info.data_source = AUDIO;
			data_source_info.audio_source_info.audio_buffer = subsampled;
			data_source_info.audio_source_info.audio_buffer_length = (PDM_BUF_SIZE/DECIMATION)*2; //sizeof(subsampled);
			err_code = app_sched_event_put(&data_source_info, sizeof(data_source_info), sd_write);
			APP_ERROR_CHECK(err_code);
		}
		else
		{
			NRF_LOG_ERROR("dropped audio sample");
			err_code = sampling_stop_microphone();
			err_code |= sampling_start_microphone(-1);
			APP_ERROR_CHECK(err_code);
		}
		break;
	}
}

static void drv_audio_pdm_event_handler(nrfx_pdm_evt_t const * const p_evt)
{
	if (p_evt->error)
	{
		NRF_LOG_ERROR("pdm handler error %ld", p_evt->error);
		return;
	}

	if(p_evt->buffer_released)
	{
		for (uint8_t l=0; l<PDM_BUF_NUM; l++)
		{
			if (pdm_buf[l].mic_buf == p_evt->buffer_released)
			{
				pdm_buf[l].released = true;
				data_source_info.audio_source_info.audio_buffer = &pdm_buf[l].mic_buf;
				NRF_LOG_INFO("pdm buf %d", pdm_buf[l].mic_buf[0]);
				process_audio_buffer();
				break;
			}
		}
	}

	if(p_evt->buffer_requested)
	{
		for (uint8_t l=0; l<PDM_BUF_NUM; l++)
		{
			if (pdm_buf[l].released)
			{
				err_code = nrfx_pdm_buffer_set(pdm_buf[l].mic_buf, PDM_BUF_SIZE);
				APP_ERROR_CHECK(err_code);
				pdm_buf[l].released = false;
				break;
			}
		}
	}
}

ret_code_t drv_audio_init(nrf_pdm_mode_t mode)
{

	switch (mode)
	{
	case 0: //stereo
		local_mode = NRF_PDM_MODE_STEREO;
		break;

	case 1: //mono
		local_mode = NRF_PDM_MODE_MONO;
		break;			
	default:
		local_mode = NRF_PDM_MODE_STEREO;
		break;
	}
	for (uint8_t l=0; l<PDM_BUF_NUM; l++)
	{
		pdm_buf[l].released = true;
	}
	data_source_info.data_source = AUDIO;

	nrfx_pdm_config_t pdm_cfg = NRFX_PDM_DEFAULT_CONFIG(MIC_CLK, MIC_DOUT);

	
	for (uint8_t f=0; f<DECIMATION; f++)
	{
		filter_weight[f] = 1.0/DECIMATION;
	}

	pdm_cfg.gain_l      = 0x45;
	pdm_cfg.gain_r      = 0x45;

	local_gain_l      = pdm_cfg.gain_l;
	local_gain_r      = pdm_cfg.gain_r ;

	pdm_cfg.mode        = local_mode;

	// 20kHz
	pdm_cfg.clock_freq	= 0x08800000;
	local_freq      = pdm_cfg.clock_freq;

	nrfx_pdm_init(&pdm_cfg, drv_audio_pdm_event_handler);

	//nrf_pdm_psel_connect(0x20, 0x1F);

	NRF_LOG_INFO("pdm_cfg: mode %d, clock_freq %d, gain_r %d, gain_l %d",pdm_cfg.mode, pdm_cfg.clock_freq, pdm_cfg.gain_r, pdm_cfg.gain_l);
	audio_switch_position =	audio_switch_get_position();

    return NRF_SUCCESS;
}

int8_t drv_audio_get_mode(void)
{
	int8_t get_mode = 1;
	if (local_mode==NRF_PDM_MODE_STEREO) get_mode = 0;
	return get_mode; //pdm_cfg.mode;
}

int8_t drv_audio_get_gain_l(void)
{
	return local_gain_l;
}

int8_t drv_audio_get_gain_r(void)
{
	return local_gain_r;
}

int16_t drv_audio_get_pdm_freq(void)
{
	int16_t freq;
	switch (local_freq) // Valid freqs
	{
	case 0x08000000: //1 MHz
		freq = 100;
		break;

	case 0x08400000: //1.032 MHz
		freq = 132;
		break;	
	case 0x08800000: //1.067 MHz
		freq = 167;
		break;			
	default:
		freq = 132;
		break;
	}
	return freq;
}