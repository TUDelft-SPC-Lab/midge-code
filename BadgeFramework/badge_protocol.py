import struct

Request_status_request_tag = 1
Request_start_microphone_request_tag = 2
Request_stop_microphone_request_tag = 3
Request_start_scan_request_tag = 4
Request_stop_scan_request_tag = 5
Request_start_imu_request_tag = 6
Request_stop_imu_request_tag = 7
Request_identify_request_tag = 27
Request_restart_request_tag = 29
Request_free_sdc_space_request_tag = 30
Request_sdc_errase_all_request_tag = 31
Request_get_imu_data_request_tag = 33

Response_status_response_tag = 1
Response_start_microphone_response_tag = 2
Response_start_scan_response_tag = 3
Response_start_imu_response_tag = 4
Response_free_sdc_space_response_tag = 5
Response_sdc_errase_all_response_tag = 32
Response_get_imu_data_response_tag = 34

class _Ostream:
	def __init__(self):
		self.buf = b''
	def write(self, data):
		self.buf += data

class _Istream:
	def __init__(self, buf):
		self.buf = buf
	def read(self, l):
		if(l > len(self.buf)):
			raise Exception("Not enough bytes in Istream to read")
		ret = self.buf[0:l]
		self.buf = self.buf[l:]
		#for i in ret:
		#	print("_Istream:",i)
		return ret

class Timestamp:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.seconds = 0
		self.ms = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_seconds(ostream)
		self.encode_ms(ostream)
		pass

	def encode_seconds(self, ostream):
		ostream.write(struct.pack('<I', self.seconds))

	def encode_ms(self, ostream):
		ostream.write(struct.pack('<H', self.ms))


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_seconds(istream)
		self.decode_ms(istream)
		pass

	def decode_seconds(self, istream):
		self.seconds= struct.unpack('<I', istream.read(4))[0]

	def decode_ms(self, istream):
		self.ms= struct.unpack('<H', istream.read(2))[0]


class BadgeAssignement:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.ID = 0
		self.group = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_ID(ostream)
		self.encode_group(ostream)
		pass

	def encode_ID(self, ostream):
		ostream.write(struct.pack('<H', self.ID))

	def encode_group(self, ostream):
		ostream.write(struct.pack('<B', self.group))


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_ID(istream)
		self.decode_group(istream)
		pass

	def decode_ID(self, istream):
		self.ID= struct.unpack('<H', istream.read(2))[0]

	def decode_group(self, istream):
		self.group= struct.unpack('<B', istream.read(1))[0]


class ScanDevice:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.ID = 0
		self.rssi = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_ID(ostream)
		self.encode_rssi(ostream)
		pass

	def encode_ID(self, ostream):
		ostream.write(struct.pack('<H', self.ID))

	def encode_rssi(self, ostream):
		ostream.write(struct.pack('<b', self.rssi))


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_ID(istream)
		self.decode_rssi(istream)
		pass

	def decode_ID(self, istream):
		self.ID= struct.unpack('<H', istream.read(2))[0]

	def decode_rssi(self, istream):
		self.rssi= struct.unpack('<b', istream.read(1))[0]



class StatusRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timestamp = None
		self.has_badge_assignement = 0
		self.badge_assignement = None
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timestamp(ostream)
		self.encode_badge_assignement(ostream)
		pass

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)

	def encode_badge_assignement(self, ostream):
		ostream.write(struct.pack('<B', self.has_badge_assignement))
		if self.has_badge_assignement:
			self.badge_assignement.encode_internal(ostream)


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timestamp(istream)
		self.decode_badge_assignement(istream)
		pass

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

	def decode_badge_assignement(self, istream):
		self.has_badge_assignement= struct.unpack('<B', istream.read(1))[0]
		if self.has_badge_assignement:
			self.badge_assignement = BadgeAssignement()
			self.badge_assignement.decode_internal(istream)


class StartMicrophoneRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timestamp = None
		self.mode = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timestamp(ostream)
		self.encode_mode(ostream)
		pass

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)

	def encode_mode(self, ostream):
		ostream.write(struct.pack('<B', self.mode))

	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timestamp(istream)
		self.decode_mode(istream)
		pass

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

	def decode_mode(self, istream):
		self.mode= struct.unpack('<B', istream.read(1))[0]

class StopMicrophoneRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		pass


class StartScanRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timestamp = None
		self.window = 0
		self.interval = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timestamp(ostream)
		self.encode_window(ostream)
		self.encode_interval(ostream)
		pass

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)

	def encode_window(self, ostream):
		ostream.write(struct.pack('<H', self.window))

	def encode_interval(self, ostream):
		ostream.write(struct.pack('<H', self.interval))

	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timestamp(istream)
		self.decode_window(istream)
		self.decode_interval(istream)
		pass

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

	def decode_window(self, istream):
		self.window= struct.unpack('<H', istream.read(2))[0]

	def decode_interval(self, istream):
		self.interval= struct.unpack('<H', istream.read(2))[0]



class StopScanRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		pass


class StartImuRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timestamp = None
		self.acc_fsr = 0
		self.gyr_fsr = 0
		self.datarate = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timestamp(ostream)
		self.encode_acc_fsr(ostream)
		self.encode_gyr_fsr(ostream)
		self.encode_datarate(ostream)
		pass

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)

	def encode_acc_fsr(self, ostream):
		ostream.write(struct.pack('<H', self.acc_fsr))

	def encode_gyr_fsr(self, ostream):
		ostream.write(struct.pack('<H', self.gyr_fsr))

	def encode_datarate(self, ostream):
		ostream.write(struct.pack('<H', self.datarate))


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timestamp(istream)
		self.decode_acc_fsr(istream)
		self.decode_gyr_fsr(istream)
		self.decode_datarate(istream)
		pass

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

	def decode_acc_fsr(self, istream):
		self.acc_fsr = struct.unpack('<H', istream.read(2))[0]

	def decode_gyr_fsr(self, istream):
		self.gyr_fsr = struct.unpack('<H', istream.read(2))[0]

	def decode_datarate(self, istream):
		self.datarate= struct.unpack('<H', istream.read(2))[0]


class StopImuRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		pass



class IdentifyRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timeout = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timeout(ostream)
		pass

	def encode_timeout(self, ostream):
		ostream.write(struct.pack('<H', self.timeout))


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timeout(istream)
		pass

	def decode_timeout(self, istream):
		self.timeout= struct.unpack('<H', istream.read(2))[0]



class RestartRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		pass


class FreeSDCSpaceRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		pass

class ErraseAllRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		pass

class GetIMUDataRequest:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		pass		

class Request:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.type = self._type()
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.type.encode_internal(ostream)
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.type.decode_internal(istream)
		pass

	class _type:

		def __init__(self):
			self.reset()

		def __repr__(self):
			return str(self.__dict__)

		def reset(self):
			self.which = 0
			self.status_request = None
			self.start_microphone_request = None
			self.stop_microphone_request = None
			self.start_scan_request = None
			self.stop_scan_request = None
			self.start_imu_request = None
			self.stop_imu_request = None
			self.identify_request = None
			self.restart_request = None
			self.free_sdc_space_request = None
			self.sdc_errase_all_request = None
			self.get_imu_data_request = None
			pass

		def encode_internal(self, ostream):
			ostream.write(struct.pack('<B', self.which))
			options = {
				1: self.encode_status_request,
				2: self.encode_start_microphone_request,
				3: self.encode_stop_microphone_request,
				4: self.encode_start_scan_request,
				5: self.encode_stop_scan_request,
				6: self.encode_start_imu_request,
				7: self.encode_stop_imu_request,
				27: self.encode_identify_request,
				29: self.encode_restart_request,
				30: self.encode_free_sdc_space_request,
				31: self.encode_sdc_errase_all_request,
				33: self.encode_get_imu_data_request,
			}
			options[self.which](ostream)
			pass

		def encode_status_request(self, ostream):
			self.status_request.encode_internal(ostream)

		def encode_start_microphone_request(self, ostream):
			self.start_microphone_request.encode_internal(ostream)

		def encode_stop_microphone_request(self, ostream):
			self.stop_microphone_request.encode_internal(ostream)

		def encode_start_scan_request(self, ostream):
			self.start_scan_request.encode_internal(ostream)

		def encode_stop_scan_request(self, ostream):
			self.stop_scan_request.encode_internal(ostream)

		def encode_start_imu_request(self, ostream):
			self.start_imu_request.encode_internal(ostream)

		def encode_stop_imu_request(self, ostream):
			self.stop_imu_request.encode_internal(ostream)

		def encode_identify_request(self, ostream):
			self.identify_request.encode_internal(ostream)

		def encode_restart_request(self, ostream):
			self.restart_request.encode_internal(ostream)

		def encode_free_sdc_space_request(self, ostream):
			self.free_sdc_space_request.encode_internal(ostream)

		def encode_sdc_errase_all_request(self, ostream):
			self.sdc_errase_all_request.encode_internal(ostream)			

		def encode_get_imu_data_request(self, ostream):
			self.get_imu_data_request.encode_internal(ostream)

		def decode_internal(self, istream):
			self.reset()
			self.which= struct.unpack('<B', istream.read(1))[0]
			options = {
				1: self.decode_status_request,
				2: self.decode_start_microphone_request,
				3: self.decode_stop_microphone_request,
				4: self.decode_start_scan_request,
				5: self.decode_stop_scan_request,
				6: self.decode_start_imu_request,
				7: self.decode_stop_imu_request,
				27: self.decode_identify_request,
				29: self.decode_restart_request,
				30: self.decode_free_sdc_space_request,
				31: self.decode_sdc_errase_all_request,
				33: self.decode_get_imu_data_request,
			}
			options[self.which](istream)
			pass

		def decode_status_request(self, istream):
			self.status_request = StatusRequest()
			self.status_request.decode_internal(istream)

		def decode_start_microphone_request(self, istream):
			self.start_microphone_request = StartMicrophoneRequest()
			self.start_microphone_request.decode_internal(istream)

		def decode_stop_microphone_request(self, istream):
			self.stop_microphone_request = StopMicrophoneRequest()
			self.stop_microphone_request.decode_internal(istream)

		def decode_start_scan_request(self, istream):
			self.start_scan_request = StartScanRequest()
			self.start_scan_request.decode_internal(istream)

		def decode_stop_scan_request(self, istream):
			self.stop_scan_request = StopScanRequest()
			self.stop_scan_request.decode_internal(istream)

		def decode_start_imu_request(self, istream):
			self.start_imu_request = StartImuRequest()
			self.start_imu_request.decode_internal(istream)

		def decode_stop_imu_request(self, istream):
			self.stop_imu_request = StopImuRequest()
			self.stop_imu_request.decode_internal(istream)

		def decode_identify_request(self, istream):
			self.identify_request = IdentifyRequest()
			self.identify_request.decode_internal(istream)

		def decode_restart_request(self, istream):
			self.restart_request = RestartRequest()
			self.restart_request.decode_internal(istream)

		def decode_free_sdc_space_request(self, istream):
			self.free_sdc_space_request = FreeSDCSpaceRequest()
			self.free_sdc_space_request.decode_internal(istream)

		def decode_sdc_errase_all_request(self, istream):
			self.sdc_errase_all_request = ErraseAllRequest()
			self.sdc_errase_all_request.decode_internal(istream)			

		def decode_get_imu_data_request(self, istream):
			self.get_imu_data_request = ErraseAllRequest()
			self.get_imu_data_request.decode_internal(istream)	


class StatusResponse:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.clock_status = 0
		self.microphone_status = 0
		self.scan_status = 0
		self.imu_status = 0
		self.battery_level = 0
		self.pdm_data = 0
		self.scan_data = 0
		self.timestamp = None
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_clock_status(ostream)
		self.encode_microphone_status(ostream)
		self.encode_scan_status(ostream)
		self.encode_imu_status(ostream)
		self.encode_timestamp(ostream)
		self.encode_battery_level(ostream)
		self.encode_pdm_data(ostream)
		self.encode_scan_data(ostream)
		pass

	def encode_clock_status(self, ostream):
		ostream.write(struct.pack('<B', self.clock_status))

	def encode_microphone_status(self, ostream):
		ostream.write(struct.pack('<B', self.microphone_status))

	def encode_scan_status(self, ostream):
		ostream.write(struct.pack('<B', self.scan_status))

	def encode_imu_status(self, ostream):
		ostream.write(struct.pack('<B', self.imu_status))

	def encode_battery_level(self, ostream):
		ostream.write(struct.pack('<B', self.battery_level))

	def encode_pdm_data(self, ostream):
		ostream.write(struct.pack('<h', self.pdm_data))

	def encode_scan_data(self, ostream):
		ostream.write(struct.pack('<b', self.scan_data))		

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_clock_status(istream)
		self.decode_microphone_status(istream)
		self.decode_scan_status(istream)
		self.decode_imu_status(istream)
		self.decode_battery_level(istream)
		self.decode_pdm_data(istream)
		self.decode_timestamp(istream)
		self.decode_scan_data(istream)
		pass

	def decode_clock_status(self, istream):
		#print("decode_clock_status:", istream.buf)
		#print("decode_clock_status:", istream.read(1))
		self.clock_status= struct.unpack('<B', istream.buf[3])[0]

	def decode_microphone_status(self, istream):
		#print("decode_microphone_status: ", i)
		self.microphone_status= struct.unpack('<B', istream.buf[4])[0]

	def decode_scan_status(self, istream):
		#print("decode_scan_status: ", i)
		self.scan_status= struct.unpack('<B', istream.buf[5])[0]

	def decode_imu_status(self, istream):
		#print("decode_imu_status: ", i)
		self.imu_status= struct.unpack('<B', istream.buf[6])[0]

	def decode_battery_level(self, istream):
		#print("decode_battery_level: ", i)
		self.battery_level= struct.unpack('<B', istream.buf[7])[0]

	def decode_pdm_data(self, istream):
		self.pdm_data= (struct.unpack('<b', istream.buf[13])[0] << 16) + (struct.unpack('<B', (istream.buf[12]))[0]<< 8)+ struct.unpack('<B', (istream.buf[11]))[0]

	def decode_scan_data(self, istream):
		self.scan_data= (struct.unpack('<b', istream.buf[10])[0] << 8) + struct.unpack('<B', (istream.buf[9]))[0]

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)


class StartMicrophoneResponse:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timestamp = None
		self.mode = 0
		self.switch_pos = 0
		self.gain_l = 0
		self.gain_r = 0
		self.pdm_freq = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timestamp(ostream)
		self.encode_mode(ostream)
		self.encode_switch_pos(ostream)
		self.encode_gain_l(ostream)
		self.encode_gain_r(ostream)
		self.encode_pdm_freq(ostream)
		pass

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)

	def encode_mode(self, ostream):
		ostream.write(struct.pack('<b', self.mode))

	def encode_switch_pos(self, ostream):
		ostream.write(struct.pack('<b', self.switch_pos))

	def encode_gain_l(self, ostream):
		ostream.write(struct.pack('<b', self.gain_l))

	def encode_gain_r(self, ostream):
		ostream.write(struct.pack('<b', self.gain_r))	

	def encode_pdm_freq(self, ostream):
		ostream.write(struct.pack('<B', self.pdm_freq))				


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timestamp(istream)
		self.decode_mode(istream)
		self.decode_switch_pos(istream)
		self.decode_gain_l(istream)
		self.decode_gain_r(istream)
		self.decode_pdm_freq(istream)
		pass

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

	def decode_mode(self, istream):
		self.mode= struct.unpack('<b', istream.buf[3])[0]

	def decode_gain_l(self, istream):
		self.gain_l= struct.unpack('<b', istream.buf[4])[0]

	def decode_gain_r(self, istream):
		self.gain_r= struct.unpack('<b', istream.buf[5])[0]

	def decode_switch_pos(self, istream):
		self.switch_pos= struct.unpack('<b', istream.buf[6])[0]

	def decode_pdm_freq(self, istream):
		#print("decode_pdm_freq: ", istream.buf)
		self.pdm_freq= struct.unpack('<B', istream.buf[7])[0]+900


class StartScanResponse:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timestamp = None
		self.window = 0
		self.interval = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timestamp(ostream)
		self.encode_window(ostream)
		self.encode_interval(ostream)
		pass

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)

	def encode_window(self, ostream):
		self.window.encode_internal(ostream)
	
	def encode_interval(self, ostream):
		self.interval.encode_internal(ostream)


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timestamp(istream)
		self.decode_window(istream)
		self.decode_interval(istream)		
		pass

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

	def decode_window(self, istream):
		self.window= (struct.unpack('<B', istream.buf[4])[0] << 8) + struct.unpack('<B', (istream.buf[3]))[0]
		
	def decode_interval(self, istream):
		self.interval= (struct.unpack('<B', istream.buf[6])[0] << 8) + struct.unpack('<B', (istream.buf[5]))[0]


class StartImuResponse:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.timestamp = None
		self.self_test_done = 0
		self.gyr_fsr = 0
		self.acc_fsr = 0
		self.datarate = 0
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_timestamp(ostream)
		self.encode_gyr_fsr(ostream)
		self.encode_acc_fsr(ostream)
		self.encode_self_test_done(ostream)
		self.encode_datarate(ostream)
		pass

	def encode_self_test_done(self, ostream):
		self.self_test_done.encode_internal(ostream)

	def encode_acc_fsr(self, ostream):
		self.acc_fsr.encode_internal(ostream)

	def encode_gyr_fsr(self, ostream):
		self.gyr_fsr.encode_internal(ostream)

	def encode_datarate(self, ostream):
		self.datarate.encode_internal(ostream)				


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_timestamp(istream)
		self.decode_self_test_done(istream)
		self.decode_acc_fsr(istream)
		self.decode_gyr_fsr(istream)
		self.decode_datarate(istream)
		pass

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

	def decode_self_test_done(self, istream):
		self.self_test_done= struct.unpack('<B', istream.buf[3])[0]

	def decode_acc_fsr(self, istream):
		self.gyr_fsr = (struct.unpack('<B', istream.buf[8])[0] << 32) + (struct.unpack('<B', istream.buf[7])[0] << 16) + (struct.unpack('<B', istream.buf[6])[0] << 8) + (struct.unpack('<B', (istream.buf[5]))[0])

	def decode_gyr_fsr(self, istream):
		self.acc_fsr = (struct.unpack('<B', istream.buf[12])[0] << 32) + (struct.unpack('<B', istream.buf[11])[0] << 16) + (struct.unpack('<B', istream.buf[10])[0] << 8) + (struct.unpack('<B', (istream.buf[9]))[0])

	def decode_datarate(self, istream):
		#print("datarate:", istream.buf)
		self.datarate = struct.unpack('<B', istream.buf[13])[0]


class FreeSDCSpaceResponse:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.total_space = 0
		self.free_space = 0
		self.timestamp = None
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_total_space(ostream)
		self.encode_free_space(ostream)
		self.encode_timestamp(ostream)
		pass

	def encode_total_space(self, ostream):
		ostream.write(struct.pack('<I', self.total_space))

	def encode_free_space(self, ostream):
		ostream.write(struct.pack('<I', self.free_space))

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_total_space(istream)
		self.decode_free_space(istream)
		self.decode_timestamp(istream)
		pass

	def decode_total_space(self, istream):
		print(" total space",istream.buf)
		self.total_space= (struct.unpack('<b', istream.buf[6])[0] << 32) + (struct.unpack('<b', istream.buf[5])[0] << 16) + (struct.unpack('<b', istream.buf[4])[0] << 8) + (struct.unpack('<b', (istream.buf[3]))[0])

	def decode_free_space(self, istream):
		self.free_space= (struct.unpack('<b', istream.buf[10])[0] << 32) + (struct.unpack('<b', istream.buf[9])[0] << 16) + (struct.unpack('<b', istream.buf[8])[0] << 8) + (struct.unpack('<b', (istream.buf[7]))[0])

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)

class ErraseAllResponse:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.done_errase = 0
		self.timestamp = None
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_done_errase(ostream)
		self.encode_timestamp(ostream)
		pass

	def encode_done_errase(self, ostream):
		ostream.write(struct.pack('<B', self.done_errase))

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_done_errase(istream)
		self.decode_timestamp(istream)
		pass

	def decode_done_errase(self, istream):
		self.done_errase= struct.unpack('<B', istream.buf[3])[0]

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)		

#
class GetIMUDataResponse:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.gyr_x = 0
		self.gyr_y = 0
		self.gyr_z = 0

		self.mag_x = 0
		self.mag_y = 0
		self.mag_z = 0

		self.acc_x = 0
		self.acc_y = 0
		self.acc_z = 0		

		self.rot_x = 0
		self.rot_y = 0
		self.rot_z = 0		
		self.timestamp = None
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.encode_gyr_x(ostream)
		self.encode_gyr_y(ostream)
		self.encode_gyr_z(ostream)
		self.encode_mag_x(ostream)
		self.encode_mag_y(ostream)
		self.encode_mag_z(ostream)
		self.encode_acc_x(ostream)
		self.encode_acc_y(ostream)
		self.encode_acc_z(ostream)
		self.encode_rot_x(ostream)
		self.encode_rot_y(ostream)
		self.encode_rot_z(ostream)
		self.encode_timestamp(ostream)
		pass

	def encode_gyr_x(self, ostream):
		ostream.write(struct.pack('<B', self.gyr_x))

	def encode_gyr_y(self, ostream):
		ostream.write(struct.pack('<B', self.gyr_y))

	def encode_gyr_z(self, ostream):
		ostream.write(struct.pack('<B', self.gyr_z))

	def encode_mag_x(self, ostream):
		ostream.write(struct.pack('<B', self.mag_x))

	def encode_mag_y(self, ostream):
		ostream.write(struct.pack('<B', self.mag_y))

	def encode_mag_z(self, ostream):
		ostream.write(struct.pack('<B', self.mag_z))

	def encode_acc_x(self, ostream):
		ostream.write(struct.pack('<B', self.acc_x))

	def encode_acc_y(self, ostream):
		ostream.write(struct.pack('<B', self.acc_y))

	def encode_acc_z(self, ostream):
		ostream.write(struct.pack('<B', self.acc_z))

	def encode_rot_x(self, ostream):
		ostream.write(struct.pack('<B', self.rot_x))

	def encode_rot_y(self, ostream):
		ostream.write(struct.pack('<B', self.rot_y))

	def encode_rot_z(self, ostream):
		ostream.write(struct.pack('<B', self.rot_z))

	def encode_timestamp(self, ostream):
		self.timestamp.encode_internal(ostream)


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.decode_gyr_x(istream)
		self.decode_gyr_y(istream)
		self.decode_gyr_z(istream)
		self.decode_mag_x(istream)
		self.decode_mag_y(istream)
		self.decode_mag_z(istream)
		self.decode_acc_x(istream)
		self.decode_acc_y(istream)
		self.decode_acc_z(istream)
		self.decode_rot_x(istream)
		self.decode_rot_y(istream)
		self.decode_rot_z(istream)
		self.decode_timestamp(istream)
		pass

	def decode_gyr_x(self, istream):		
		self.gyr_x= float((struct.unpack('<b', istream.buf[4])[0] << 8) + struct.unpack('<B', (istream.buf[3]))[0])/float(10000)

	def decode_gyr_y(self, istream):
		self.gyr_y= float((struct.unpack('<b', istream.buf[6])[0] << 8) + struct.unpack('<B', (istream.buf[5]))[0])/float(10000)

	def decode_gyr_z(self, istream):
		self.gyr_z= float((struct.unpack('<b', istream.buf[8])[0] << 8) + struct.unpack('<B', (istream.buf[7]))[0])/float(10000)

	def decode_mag_x(self, istream):
		self.mag_x= float((struct.unpack('<b', istream.buf[10])[0] << 8) + struct.unpack('<B', (istream.buf[9]))[0])/float(10000)

	def decode_mag_y(self, istream):
		self.mag_y= float((struct.unpack('<b', istream.buf[12])[0] << 8) + struct.unpack('<B', (istream.buf[11]))[0])/float(10000)

	def decode_mag_z(self, istream):
		self.mag_z= float((struct.unpack('<b', istream.buf[14])[0] << 8) + struct.unpack('<B', (istream.buf[13]))[0])/float(10000)

	def decode_acc_x(self, istream):
		self.acc_x= float((struct.unpack('<b', istream.buf[16])[0] << 8) + struct.unpack('<B', (istream.buf[15]))[0])/float(10000)

	def decode_acc_y(self, istream):
		self.acc_y= float((struct.unpack('<b', istream.buf[18])[0] << 8) + struct.unpack('<B', (istream.buf[17]))[0])/float(10000)

	def decode_acc_z(self, istream):
		self.acc_z= float((struct.unpack('<b', istream.buf[20])[0] << 8) + struct.unpack('<B', (istream.buf[19]))[0])/float(10000)

	def decode_rot_x(self, istream):
		self.rot_x= float((struct.unpack('<b', istream.buf[22])[0] << 8) + struct.unpack('<B', (istream.buf[21]))[0])/float(10000)

	def decode_rot_y(self, istream):
		self.rot_y= float((struct.unpack('<b', istream.buf[24])[0] << 8) + struct.unpack('<B', (istream.buf[23]))[0])/float(10000)

	def decode_rot_z(self, istream):
		self.rot_z= float((struct.unpack('<b', istream.buf[26])[0] << 8) + struct.unpack('<B', (istream.buf[25]))[0])/float(10000)

	def decode_timestamp(self, istream):
		self.timestamp = Timestamp()
		self.timestamp.decode_internal(istream)	



class Response:

	def __init__(self):
		self.reset()

	def __repr__(self):
		return str(self.__dict__)

	def reset(self):
		self.type = self._type()
		pass

	def encode(self):
		ostream = _Ostream()
		self.encode_internal(ostream)
		return ostream.buf

	def encode_internal(self, ostream):
		self.type.encode_internal(ostream)
		pass


	@classmethod
	def decode(cls, buf):
		obj = cls()
		obj.decode_internal(_Istream(buf))
		return obj

	def decode_internal(self, istream):
		self.reset()
		self.type.decode_internal(istream)
		pass

	class _type:

		def __init__(self):
			self.reset()

		def __repr__(self):
			return str(self.__dict__)

		def reset(self):
			self.which = 0
			self.status_response = None
			self.start_microphone_response = None
			self.start_scan_response = None
			self.start_imu_response = None
			self.free_sdc_space_response = None
			self.sdc_errase_all_response = None
			self.get_imu_data_response = None
			pass

		def encode_internal(self, ostream):
			ostream.write(struct.pack('<B', self.which))
			options = {
				1: self.encode_status_response,
				2: self.encode_start_microphone_response,
				3: self.encode_start_scan_response,
				4: self.encode_start_imu_response,
				5: self.encode_free_sdc_space_response,
				32: self.encode_sdc_errase_all_response,
				34: self.encode_get_imu_data_response,
			}
			options[self.which](ostream)
			pass

		def encode_status_response(self, ostream):
			self.status_response.encode_internal(ostream)

		def encode_start_microphone_response(self, ostream):
			self.start_microphone_response.encode_internal(ostream)

		def encode_start_scan_response(self, ostream):
			self.start_scan_response.encode_internal(ostream)

		def encode_start_imu_response(self, ostream):
			self.start_imu_response.encode_internal(ostream)

		def encode_free_sdc_space_response(self, ostream):
			self.free_sdc_space_response.encode_internal(ostream)

		def encode_sdc_errase_all_response(self, ostream):
			self.sdc_errase_all_response.encode_internal(ostream)			

		def encode_get_imu_data(self, ostream):
			self.get_imu_data.encode_internal(ostream)	

		def decode_internal(self, istream):
			self.reset()
			self.which= struct.unpack('<B', istream.read(1))[0]
			options = {
				1: self.decode_status_response,
				2: self.decode_start_microphone_response,
				3: self.decode_start_scan_response,
				4: self.decode_start_imu_response,
				5: self.decode_free_sdc_space_response,
				32: self.decode_sdc_errase_all_response,
				34: self.decode_get_imu_data_response,
			}
			options[self.which](istream)
			pass

		def decode_status_response(self, istream):
			self.status_response = StatusResponse()
			self.status_response.decode_internal(istream)

		def decode_start_microphone_response(self, istream):
			self.start_microphone_response = StartMicrophoneResponse()
			self.start_microphone_response.decode_internal(istream)

		def decode_start_scan_response(self, istream):
			self.start_scan_response = StartScanResponse()
			self.start_scan_response.decode_internal(istream)

		def decode_start_imu_response(self, istream):
			self.start_imu_response = StartImuResponse()
			self.start_imu_response.decode_internal(istream)

		def decode_free_sdc_space_response(self, istream):
			self.free_sdc_space_response = FreeSDCSpaceResponse()
			self.free_sdc_space_response.decode_internal(istream)

		def decode_sdc_errase_all_response(self, istream):
			self.sdc_errase_all_response = ErraseAllResponse()
			self.sdc_errase_all_response.decode_internal(istream)			

		def decode_get_imu_data_response(self, istream):
			self.get_imu_data_response = GetIMUDataResponse()
			self.get_imu_data_response.decode_internal(istream)			