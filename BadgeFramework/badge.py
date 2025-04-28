from __future__ import division, absolute_import, print_function
import time
import logging
import sys
import struct
import queue as Queue
import utils
from bleak import BleakClient, BLEDevice, BleakGATTCharacteristic
from typing import Union

CONNECTION_RETRY_TIMES = 15
DEFAULT_SCAN_WINDOW = 250
DEFAULT_SCAN_INTERVAL = 1000

DEFAULT_IMU_ACC_FSR = 4  # Valid ranges: 2, 4, 8, 16
DEFAULT_IMU_GYR_FSR = 1000  # Valid ranges: 250, 500, 1000, 2000
DEFAULT_IMU_DATARATE = 50

DEFAULT_MICROPHONE_MODE = 0	#Valid options: 0=Stereo, 1=Mono

from badge_protocol import *

logger = logging.getLogger(__name__)

# logging.basicConfig(
#     level=logging.DEBUG,  # or logging.INFO for less verbosity
#     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
# )

# -- Helper methods used often in badge communication -- 

# We generally define timestamp_seconds to be in number of seconds since UTC epoch
# and timestamp_miliseconds to be the miliseconds portion of that UTC timestamp.

# Returns the current timestamp as two parts - seconds and milliseconds
def get_timestamps():
    return get_timestamps_from_time(time.time())

# Returns the given time as two parts - seconds and milliseconds
def get_timestamps_from_time(t):
    timestamp_seconds = int(t)
    timestamp_fraction_of_second = t - timestamp_seconds
    timestamp_ms = int(1000 * timestamp_fraction_of_second)
    return (timestamp_seconds, timestamp_ms)


# Convert badge timestamp representation to python representation
def timestamps_to_time(timestamp_seconds, timestamp_miliseconds):
    return float(timestamp_seconds) + (float(timestamp_miliseconds) / 1000.0)


# Represents an OpenBadge currently connected via the BadgeConnection 'connection'.
#    The 'connection' should already be connected when it is used to initialize this class.
# Implements methods that allow for interaction with that badge. 
class OpenBadge(object):
    def __init__(self, device: Union[BLEDevice, int], mac_address: str = None):
        # self.connection = connection
        self.status_response_queue = Queue.Queue()
        self.start_microphone_response_queue = Queue.Queue()
        self.start_scan_response_queue = Queue.Queue()
        self.start_imu_response_queue = Queue.Queue()
        self.free_sdc_space_response_queue = Queue.Queue()
        self.sdc_errase_all_response_queue = Queue.Queue()
        self.get_imu_data_response_queue = Queue.Queue()
        self.rx_queue = Queue.Queue()

        if isinstance(device, BLEDevice):
            self.device_id = utils.get_device_id(device)
            self.address = device.address
        elif isinstance(device, int):
            self.device_id = device
            self.address = mac_address
        else:
            raise TypeError
        self.client = BleakClient(self.address, disconnected_callback=self.badge_disconnected)

    async def __aenter__(self):
        for _ in range(CONNECTION_RETRY_TIMES):
            try:
                await self.client.connect(timeout=1000)
                await self.client.start_notify(utils.RX_CHAR_UUID, self.received_callback)
                return self
            except Exception as e:
                pass
        raise TimeoutError(f'Failed to connect to device after {CONNECTION_RETRY_TIMES} attempts.')

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()

    @property
    def is_connected(self) -> bool:
        return self.client.is_connected

    def badge_disconnected(self, b: BleakClient) -> None:
        """disconnection callback"""
        print(f"Warning: disconnected badge")
    
    def received_callback(self, sender: BleakGATTCharacteristic, message: bytearray):
        logger.debug("Recieved {}".format(message.hex()))
        for b in message:
            self.rx_queue.put(b)
        

    # Helper function to send a BadgeMessage `command_message` to a device, expecting a response
    # of class `response_type` that is a subclass of BadgeMessage, or None if no response is expected.
    async def send_command(self, command_message, response_type):
        serialized_command = command_message.serialize_message()
        logger.debug(
            "Sending: {}, Raw: {}".format(
                command_message, serialized_command.hex()
            )
        )
        await self.client.write_gatt_char(utils.TX_CHAR_UUID, serialized_command, response=True)
        
    
    async def send_request(self, request_message):
        serialized_request = request_message.encode()
        # Adding length header:
        serialized_request_len = struct.pack("<H", len(serialized_request))
        serialized_request = serialized_request_len + serialized_request

        logger.debug(
            "Sending: {}, Raw: {}".format(
                request_message, serialized_request.hex()
            )
        )
        await self.client.write_gatt_char(utils.TX_CHAR_UUID, serialized_request, response=True)
        # self.connection.send(serialized_request, response_len=0)

    async def await_data(self, data_len):
        if not self.is_connected:
            raise RuntimeError("BLEBadgeConnection not connected before await_data()!")
        rx_message = bytearray()
        rx_bytes_expected = data_len
        
        if rx_bytes_expected > 0:
            while True:
                while(not self.rx_queue.empty()):
                    rx_message.append(self.rx_queue.get())
                    if(len(rx_message) == rx_bytes_expected):
                        return rx_message

                response_rx = await self.client.read_gatt_char(utils.RX_CHAR_UUID)

    async def receive_response(self):
        response_len = struct.unpack("<H", await self.await_data(2))[0]
        logger.debug("Wait response len: " + str(response_len))
        serialized_response = await self.await_data(response_len)

        response_message = Response.decode(serialized_response)

        queue_options = {
            Response_status_response_tag: self.status_response_queue,
            Response_start_microphone_response_tag: self.start_microphone_response_queue,
            Response_start_scan_response_tag: self.start_scan_response_queue,
            Response_start_imu_response_tag: self.start_imu_response_queue,
            Response_free_sdc_space_response_tag: self.free_sdc_space_response_queue,
            Response_sdc_errase_all_response_tag: self.sdc_errase_all_response_queue,
            Response_get_imu_data_response_tag: self.get_imu_data_response_queue,
        }
        response_options = {
            Response_status_response_tag: response_message.type.status_response,
            Response_start_microphone_response_tag: response_message.type.start_microphone_response,
            Response_start_scan_response_tag: response_message.type.start_scan_response,
            Response_start_imu_response_tag: response_message.type.start_imu_response,
            Response_free_sdc_space_response_tag: response_message.type.free_sdc_space_response,
            Response_sdc_errase_all_response_tag: response_message.type.sdc_errase_all_response,
            Response_get_imu_data_response_tag: response_message.type.get_imu_data_response
        }
        queue_options[response_message.type.which].put(
            response_options[response_message.type.which]
        )

    # Sends a status request to this Badge.
    #   Optional fields new_id and new_group number will set the badge's id
    #     and group number. They must be sent together.
    # Returns a StatusResponse() representing badge's response.
    async def get_status(self, t=None, new_id=None, new_group_number=None):
        if t is None:
            (timestamp_seconds, timestamp_ms) = get_timestamps()
        else:
            (timestamp_seconds, timestamp_ms) = get_timestamps_from_time(t)

        request = Request()
        request.type.which = Request_status_request_tag
        request.type.status_request = StatusRequest()
        request.type.status_request.timestamp = Timestamp()
        request.type.status_request.timestamp.seconds = timestamp_seconds
        request.type.status_request.timestamp.ms = timestamp_ms
        if not ((new_id is None) or (new_group_number is None)):
            request.type.status_request.badge_assignement = BadgeAssignement()
            request.type.status_request.badge_assignement.ID = new_id
            request.type.status_request.badge_assignement.group = new_group_number
            request.type.status_request.has_badge_assignement = True

        await self.send_request(request)

        # Clear the queue before receiving
        with self.status_response_queue.mutex:
            self.status_response_queue.queue.clear()

        while self.status_response_queue.empty():
            await self.receive_response()

        return self.status_response_queue.get()

    # Sends a request to the badge to start recording microphone data.
    # Returns a StartRecordResponse() representing the badges response.
    async def start_microphone(self, t=None, mode=DEFAULT_MICROPHONE_MODE):
        if t is None:
            (timestamp_seconds, timestamp_ms) = get_timestamps()
        else:
            (timestamp_seconds, timestamp_ms) = get_timestamps_from_time(t)
        #print("MODE ",mode)
        request = Request()
        request.type.which = Request_start_microphone_request_tag
        request.type.start_microphone_request = StartMicrophoneRequest()
        request.type.start_microphone_request.timestamp = Timestamp()
        request.type.start_microphone_request.timestamp.seconds = timestamp_seconds
        request.type.start_microphone_request.timestamp.ms = timestamp_ms
        request.type.start_microphone_request.mode = mode

        await self.send_request(request)

        with self.start_microphone_response_queue.mutex:
            self.start_microphone_response_queue.queue.clear()

        while self.start_microphone_response_queue.empty():
            await self.receive_response()

        return self.start_microphone_response_queue.get()

    # Sends a request to the badge to stop recording.
    # Returns True if request was successfuly sent.
    async def stop_microphone(self):

        request = Request()
        request.type.which = Request_stop_microphone_request_tag
        request.type.stop_microphone_request = StopMicrophoneRequest()

        await self.send_request(request)

    # Sends a request to the badge to start performing scans and collecting scan data.
    #   window_miliseconds and interval_miliseconds controls radio duty cycle during scanning (0 for firmware default)
    #     radio is active for [window_miliseconds] every [interval_miliseconds]
    # Returns a StartScanningResponse() representing the badge's response.
    async def start_scan(
        self, t=None, window_ms=DEFAULT_SCAN_WINDOW, interval_ms=DEFAULT_SCAN_INTERVAL
    ):
        if t is None:
            (timestamp_seconds, timestamp_ms) = get_timestamps()
        else:
            (timestamp_seconds, timestamp_ms) = get_timestamps_from_time(t)

        request = Request()
        request.type.which = Request_start_scan_request_tag
        request.type.start_scan_request = StartScanRequest()
        request.type.start_scan_request.timestamp = Timestamp()
        request.type.start_scan_request.timestamp.seconds = timestamp_seconds
        request.type.start_scan_request.timestamp.ms = timestamp_ms
        request.type.start_scan_request.window = window_ms
        request.type.start_scan_request.interval = interval_ms

        await self.send_request(request)

        # Clear the queue before receiving
        with self.start_scan_response_queue.mutex:
            self.start_scan_response_queue.queue.clear()

        while self.start_scan_response_queue.empty():
            await self.receive_response()

        return self.start_scan_response_queue.get()

    # Sends a request to the badge to stop scanning.
    # Returns True if request was successfuly sent.
    async def stop_scan(self):

        request = Request()
        request.type.which = Request_stop_scan_request_tag
        request.type.stop_scan_request = StopScanRequest()

        await self.send_request(request)

    async def start_imu(
        self,
        t=None,
        acc_fsr=DEFAULT_IMU_ACC_FSR,
        gyr_fsr=DEFAULT_IMU_GYR_FSR,
        datarate=DEFAULT_IMU_DATARATE,
    ):
        if t is None:
            (timestamp_seconds, timestamp_ms) = get_timestamps()
        else:
            (timestamp_seconds, timestamp_ms) = get_timestamps_from_time(t)

        request = Request()
        request.type.which = Request_start_imu_request_tag
        request.type.start_imu_request = StartImuRequest()
        request.type.start_imu_request.timestamp = Timestamp()
        request.type.start_imu_request.timestamp.seconds = timestamp_seconds
        request.type.start_imu_request.timestamp.ms = timestamp_ms
        request.type.start_imu_request.acc_fsr = acc_fsr
        request.type.start_imu_request.gyr_fsr = gyr_fsr
        request.type.start_imu_request.datarate = datarate

        await self.send_request(request)

        # Clear the queue before receiving
        with self.start_imu_response_queue.mutex:
            self.start_imu_response_queue.queue.clear()

        while self.start_imu_response_queue.empty():
            await self.receive_response()

        return self.start_imu_response_queue.get()

    async def stop_imu(self):

        request = Request()
        request.type.which = Request_stop_imu_request_tag
        request.type.stop_imu_request = StopImuRequest()

        await self.send_request(request)

    # Send a request to the badge to light an led to identify its self.
    #   If duration_seconds == 0, badge will turn off LED if currently lit.
    # Returns True if request was successfuly sent.
    async def identify(self, duration_seconds=10):

        request = Request()
        request.type.which = Request_identify_request_tag
        request.type.identify_request = IdentifyRequest()
        request.type.identify_request.timeout = duration_seconds

        await self.send_request(request)

        return True

    async def restart(self):

        request = Request()
        request.type.which = Request_restart_request_tag
        request.type.restart_request = RestartRequest()

        await self.send_request(request)

        return True

    async def get_free_sdc_space(self):

        request = Request()
        request.type.which = Request_free_sdc_space_request_tag
        request.type.free_sdc_space_request = FreeSDCSpaceRequest()

        await self.send_request(request)

        # Clear the queue before receiving
        with self.free_sdc_space_response_queue.mutex:
            self.free_sdc_space_response_queue.queue.clear()

        while self.free_sdc_space_response_queue.empty():
            await self.receive_response()

        return self.free_sdc_space_response_queue.get()


    async def sdc_errase_all(self):

        request = Request()
        request.type.which = Request_sdc_errase_all_request_tag
        request.type.sdc_errase_all_request = ErraseAllRequest()

        await self.send_request(request)

        # Clear the queue before receiving
        with self.sdc_errase_all_response_queue.mutex:
            self.sdc_errase_all_response_queue.queue.clear()

        while self.sdc_errase_all_response_queue.empty():
            await self.receive_response()

        return self.sdc_errase_all_response_queue.get()

    async def get_imu_data(self):

        request = Request()
        request.type.which = Request_get_imu_data_request_tag
        request.type.get_imu_data_request = GetIMUDataRequest()
        request.type.get_imu_data_request.timestamp = Timestamp()

        await self.send_request(request)

        # Clear the queue before receiving
        with self.get_imu_data_response_queue.mutex:
            self.get_imu_data_response_queue.queue.clear()

        while self.get_imu_data_response_queue.empty():
            await self.receive_response()

        return self.get_imu_data_response_queue.get()