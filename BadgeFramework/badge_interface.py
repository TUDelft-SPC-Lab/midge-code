from badge import *
# from ble_badge_connection import *
from dataclasses import dataclass

# Add a mock status class
@dataclass
class MockStatusResponse:
    battery_level: int = 100
    clock_status: bool = False
    imu_status: bool = False
    microphone_status: bool = False

class BadgeInterface():
    def __init__(self, address):
        self.address = address
        self.connection = None
        self.badge = None
        # Add a mock status that can be updated
        self._mock_status = MockStatusResponse()

    def connect(self):
        # self.connection = BLEBadgeConnection.get_connection_to_badge(self.address)
        # self.connection.connect()
        # self.badge = OpenBadge(self.connection)
        pass
        # print("Connected!")

    async def get_status(self):
        try:
            async with OpenBadge(0, self.address) as badge:
                return await badge.get_status()
        except Exception as e:
            print(f"Using mock status due to: {e}")
            return self._mock_status
    
    async def get_free_sdc_space(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.get_free_sdc_space()
    
    async def start_imu(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.start_imu()
    
    async def start_microphone(self, mode):
        #print("MODE interface ",mode)
        async with OpenBadge(0, self.address) as badge:
            return await badge.start_microphone(mode=mode)
    
    async def stop_microphone(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.stop_microphone()
    
    async def stop_imu(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.stop_imu()
    
    async def start_scan(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.start_scan()
    
    async def stop_scan(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.stop_scan()
    
    async def get_imu_data(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.get_imu_data()
    
    async def sdc_errase_all(self):
        async with OpenBadge(0, self.address) as badge:
            return await badge.sdc_errase_all()
    
    