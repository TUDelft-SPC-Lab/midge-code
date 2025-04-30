import tkinter as tk
import tkinter.ttk
from tkinter import Label, Button, Canvas
import tkinter.font
import random
import time
import csv
from badge_interface import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import asyncio
from asyncio import get_event_loop_policy
from dataclasses import dataclass

DEFAULT_RADIUS = 20
GET_STATUS_MAIN = True

def calculate_color(status):
    if status == 1:
        return "green"
    else:
        return "red"

class Circle(Canvas):
    def __init__(self, parent, radius=DEFAULT_RADIUS, status=0):
        Canvas.__init__(self, parent, width=2 * radius, height=2 * radius, bd=0, highlightthickness=0)
        self.radius = radius
        self.status = status
        self.color = calculate_color(self.status)
        self.create_oval(0, 0, 2 * radius, 2 * radius, fill=self.color)  # Draw a circular shape

    def update_status(self, new_status):
        self.status = new_status
        self.color = calculate_color(self.status)
        self.create_oval(0, 0, 2 * self.radius, 2 * self.radius, fill=self.color)

class CustomComponent(tk.Frame):
    def __init__(self, parent, name, badge, address, gui_instance):
        tk.Frame.__init__(self, parent, pady=10) 
        self.parent = parent
        self.gui = gui_instance  # Store reference to main GUI
        self.loop = self.gui.loop  # Get loop from GUI instance
        self.name = name
        self.badge = badge
        self.address = address
        # Initialize with default values
        self.badge_status = MockStatusResponse()  # Use the mock status as default
        self.free_space = 0
        self.new_window = {}
        self.scan_info = {'window': '', 'interval': ''}
        self.mic_info = {'mode': '', 'gain_r': '', 'gain_l': '', 'switch_pos': '', 'pdm_freq': ''}
        self.initUI()

    def initUI(self):
        # Device info
        self.badgeId = Label(self, text="Badge ID: {}".format(self.name))
        self.badgeId.grid(row=0, column=0, padx=10, pady=5)
        self.midge = Label(self, text=self.address, font=tkinter.font.Font(size=12))
        self.midge.grid(row=1, column=0, padx=10, pady=5)
        self.battery = Label(self, text='Battery: Connecting...', relief="solid")
        self.battery.grid(row=2, column=0, padx=10, pady=5)

        # Status
        self.statusLabel = Label(self, text="Status")
        self.statusLabel.grid(row=0, column=1, padx=10, pady=5)
        self.statusCircle = Circle(self, status=self.badge_status.clock_status)
        self.statusCircle.grid(row=1, column=1, padx=10, pady=5)

        # IMU
        self.IMULabel = Label(self, text="IMU")
        self.IMULabel.grid(row=0, column=2, columnspan=2, padx=10, pady=5)
        self.IMUCircle = Circle(self, status=self.badge_status.imu_status)
        self.IMUCircle.grid(row=1, column=2, columnspan=2, padx=10, pady=5)
        self.IMUStartButton = Button(self, text="Start", command=lambda: self.button_click_handler(self.start_imu))
        self.IMUStartButton.grid(row=2, column=2, padx=10, pady=5)
        self.IMUStopButton = Button(self, text="Stop", command=lambda: self.button_click_handler(self.stop_imu))
        self.IMUStopButton.grid(row=2, column=3, padx=10, pady=5)

        # Mic
        self.MicLabel = Label(self, text="Microphones")
        self.MicLabel.grid(row=0, column=4, columnspan=2, padx=10, pady=5)
        self.MicCircle = Circle(self, status=False)  # Start inactive
        self.MicCircle.grid(row=1, column=4, columnspan=2, padx=10, pady=5)
        self.MicStartMonoButton = Button(self, text="Start mono", 
            command=lambda: self.button_click_handler(self.start_microphone, None, 1))
        self.MicStartMonoButton.grid(row=2, column=4, padx=10, pady=5)
        self.MicStartStereoButton = Button(self, text="Start stereo", 
            command=lambda: self.button_click_handler(self.start_microphone, None, 0))
        self.MicStartStereoButton.grid(row=2, column=5, padx=10, pady=5)
        self.MicStopButton = Button(self, text="Stop", 
            command=lambda: self.button_click_handler(self.stop_microphone))
        self.MicStopButton.grid(row=3, column=4, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Scan
        self.ScanLabel = Label(self, text="Scanner")
        self.ScanLabel.grid(row=0, column=6, columnspan=2, padx=10, pady=5)
        self.ScanCircle = Circle(self, status=False)  # Start inactive
        self.ScanCircle.grid(row=1, column=6, columnspan=2, padx=10, pady=5)
        self.ScanStartButton = Button(self, text="Start", 
            command=lambda: self.button_click_handler(self.start_scan))
        self.ScanStartButton.grid(row=2, column=6, padx=10, pady=5)
        self.ScanStopButton = Button(self, text="Stop", 
            command=lambda: self.button_click_handler(self.stop_scan))
        self.ScanStopButton.grid(row=2, column=7, padx=10, pady=5)

        self.bind("<Button-1>", self.onMouseClick)  # Handle mouse click

         # Change the cursor when hovering
        self.bind("<Enter>", lambda event: self.config(cursor="hand2"))
        self.bind("<Leave>", lambda event: self.config(cursor=""))

    def onMouseClick(self, event):
        # Handle mouse click event
        self.new_window = NewWindow(self.badge, self.free_space, name=self.name, scan_info=self.scan_info, mic_info=self.mic_info)
        self.new_window.mainloop()

    async def start_imu(self):
        if self.badge_status.imu_status == 0:
            await self.badge.start_imu()
        else:
            print("IMU already started")
    
    async def stop_imu(self):
        await self.badge.stop_imu()
    
    async def start_microphone(self, t, mode):
        print('starting microphone for badge: {}'.format(self.name))
        if self.badge_status.microphone_status == 1:
            print("Microphone already started")
            return
        start_mic_response = await self.badge.start_microphone(mode)

        if (start_mic_response.switch_pos == 2): switch_pos = "HIGH"
        elif (start_mic_response.switch_pos == 1): switch_pos = "LOW"
        else: switch_pos = "OFF"

        if (start_mic_response.mode == 1): mic_mode = "mono"
        else: mic_mode = "stereo"

        self.mic_info = {'mode': mic_mode, 
                         'gain_r (dBm)': start_mic_response.gain_r, 
                         'gain_l (dBm)': start_mic_response.gain_l,
                         'switch_pos': switch_pos,
                         'pdm_freq (kHz)': start_mic_response.pdm_freq}
        try:
            self.new_window.MicConfig.info = self.mic_info
            self.new_window.initUI()
        except Exception as e:
            print('error in updating microphone config: {}'.format(e))
    
    async def stop_microphone(self):
        await self.badge.stop_microphone()

    async def start_scan(self):
        if self.badge_status.scan_status == 1:
            print("Scanner already started")
            return
        start_scan_response = await self.badge.start_scan()
        self.scan_info = {'window': start_scan_response.window, 
                          'interval': start_scan_response.interval}
        try:
            self.new_window.ScanConfig.info = self.scan_info
            self.new_window.ScanConfig.initUI()
        except:
            pass

    async def stop_scan(self):
        await self.badge.stop_scan()
    
    async def async_init(self):
        try:
            if self.badge:
                self.badge_status = await self.badge.get_status()
                self.free_space = (await self.badge.get_free_sdc_space()).free_space
            else:
                # Use mock data if no badge
                self.badge_status = MockStatusResponse()
                self.free_space = 0
        except Exception as e:
            print(f"Error in async_init: {e}")
            # Keep using mock data on error
            self.badge_status = MockStatusResponse()
            self.free_space = 0
        finally:
            # Always update UI
            self.update_ui_with_status()

    def update_ui_with_status(self):
        """Update all UI elements with actual values from badge_status"""
        try:
            self.battery.config(text='Battery: {}%'.format(self.badge_status.battery_level))
            self.statusCircle.update_status(self.badge_status.clock_status)
            self.IMUCircle.update_status(self.badge_status.imu_status)
            self.MicCircle.update_status(self.badge_status.microphone_status)
            self.ScanCircle.update_status(getattr(self.badge_status, 'scan_status', False))
        except Exception as e:
            print(f"Error updating UI: {e}")

    def button_click_handler(self, async_func, *args):
        """Wrapper to run async functions from button clicks"""
        try:
            if not self.badge:
                print("No device connected")
                return
            self.loop.create_task(async_func(*args))
        except Exception as e:
            print(f"Error in button handler: {e}")

class MatplolibFrame(tk.Frame):
    def __init__(self, parent, time, x, y, z):
        tk.Frame.__init__(self, parent, relief=tk.RIDGE)
        self.figure = Figure(figsize=(3, 1.5), dpi=100)
        self.plot = self.figure.add_subplot(111)
        self.plot.plot(time, x, label='x')
        self.plot.plot(time, y, label='y')
        self.plot.plot(time, z, label='z')
        # Adding the legend
        # Place the legend outside the plot
        self.plot.legend(fontsize='x-small')
        # Set x-axis limits if your data is not displaying correctly
        self.plot.set_xlim([min(time), max(time)])
        
        # Set x-axis labels
        self.plot.set_xticks(time)
        self.plot.set_xticklabels(time)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()

        self.canvas.get_tk_widget().grid(row=0, column=0)

class IMUConfig(tk.Frame):
    def __init__(self, parent, imu_status):
        tk.Frame.__init__(self, parent, borderwidth=1, relief="flat")
        label = Label(self, text="IMU Config")
        self.imu_status = imu_status
        self.time = LimitedQueue(4)
        self.time.enqueue(0)
        # gyr
        self.gyr_x = LimitedQueue(4)
        self.gyr_y = LimitedQueue(4)
        self.gyr_z = LimitedQueue(4)
        # rot
        self.rot_x = LimitedQueue(4)
        self.rot_y = LimitedQueue(4)
        self.rot_z = LimitedQueue(4)
        # acc
        self.acc_x = LimitedQueue(4)
        self.acc_y = LimitedQueue(4)
        self.acc_z = LimitedQueue(4)
        # mag
        self.mag_x = LimitedQueue(4)
        self.mag_y = LimitedQueue(4)
        self.mag_z = LimitedQueue(4)
        
        # Create the layout frames
        self.top_frame = tk.Frame(self, padx=5, pady=5, bg='lightgrey')
        self.table = tk.Frame(self, padx=5, pady=5, bg='lightgrey')
        self.top_frame.grid(row=0, column=0, sticky='nsew')
        self.table.grid(row=1, column=0, sticky='nsew')
        
        self.initUI()

    def initUI(self):
        info = ["acc_fsr (g): 16", "gyr_fsr (dps): 2000", "datarate: 50"]
        
        title = tk.Label(self.top_frame, text='IMU Data', font=tkinter.font.Font(size=10, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, sticky='w')
        # Create information header
        for i, text in enumerate(info):
            label = tk.Label(self.top_frame, text=text, bg='lightgrey')
            label.grid(row=i+1, column=0, columnspan=2, sticky='w')
        # Create table
        # gyr
        self.gyr_x.enqueue(self.imu_status.gyr_x)
        self.gyr_y.enqueue(self.imu_status.gyr_y)
        self.gyr_z.enqueue(self.imu_status.gyr_z)
        label = tk.Label(self.table, text="gyr (dps vs time)", relief=tk.RIDGE)
        label.grid(row=0, column=0, sticky='nsew')
        line_chart = MatplolibFrame(self.table, time=self.time.queue, x=self.gyr_x.queue, y=self.gyr_y.queue, z=self.gyr_z.queue)
        line_chart.grid(row=1, column=0)    
        # rot
        self.rot_x.enqueue(self.imu_status.rot_x)
        self.rot_y.enqueue(self.imu_status.rot_y)
        self.rot_z.enqueue(self.imu_status.rot_z)
        label = tk.Label(self.table, text="rot (rad/s vs time)", relief=tk.RIDGE)
        label.grid(row=0, column=1, sticky='nsew')
        line_chart = MatplolibFrame(self.table, time=self.time.queue, x=self.rot_x.queue, y=self.rot_y.queue, z=self.rot_z.queue)
        line_chart.grid(row=1, column=1)
        # acc
        self.acc_x.enqueue(self.imu_status.acc_x)
        self.acc_y.enqueue(self.imu_status.acc_y)
        self.acc_z.enqueue(self.imu_status.acc_z)
        label = tk.Label(self.table, text="acc (g vs time)", relief=tk.RIDGE)
        label.grid(row=2, column=0, sticky='nsew')
        line_chart = MatplolibFrame(self.table, time=self.time.queue, x=self.acc_x.queue, y=self.acc_y.queue, z=self.acc_z.queue)
        line_chart.grid(row=3, column=0)      
        # mag
        self.mag_x.enqueue(self.imu_status.mag_x)
        self.mag_y.enqueue(self.imu_status.mag_y)
        self.mag_z.enqueue(self.imu_status.mag_z)
        label = tk.Label(self.table, text="mag (uT vs time)", relief=tk.RIDGE)
        label.grid(row=2, column=1, sticky='nsew')
        line_chart = MatplolibFrame(self.table, time=self.time.queue, x=self.mag_x.queue, y=self.mag_y.queue, z=self.mag_z.queue)
        line_chart.grid(row=3, column=1)   

        self.config(bg="white", relief="solid")

class MicConfig(tk.Frame):
    def __init__(self, parent, data, info):
        tk.Frame.__init__(self, parent, borderwidth=1, relief="flat")
        self.data = data
        self.info = info
        self.initUI()

    def initUI(self):
        # Create the layout frames
        top_frame = tk.Frame(self, padx=5, pady=5, bg='lightgrey')
        table = tk.Frame(self, padx=5, pady=5, bg='lightgrey')
        top_frame.grid(row=0, column=0, sticky='nsew')
        table.grid(row=1, column=0, sticky='nsew')
        
        title = tk.Label(top_frame, text='Microphones Data', font=tkinter.font.Font(size=10, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, sticky='w')
        # Loop over the dictionary and create labels
        for i, (key, value) in enumerate(self.info.items()):
            label_text = "{}: {}".format(key, value)
            label = tk.Label(top_frame, text=label_text)
            label.grid(row=i+1, column=0, columnspan=2, sticky='w')

        for i, e in enumerate(self.data):
            label = tk.Label(table, text=str(e), relief=tk.RIDGE, width=45)
            label.grid(row=i, column=0, sticky="nsew")
    
        # Configure row and column weights to make the cells expand
        for i in range(len(self.data)):
            self.grid_rowconfigure(i, weight=1)

        self.config(bg="white", relief="solid")

# Scan 
class ScanConfig(tk.Frame):
    def __init__(self, parent, data, info):
        tk.Frame.__init__(self, parent, borderwidth=1, relief="flat")
        self.data = data
        self.info = info
        self.initUI()

    def initUI(self):
        # Create the layout frames
        top_frame = tk.Frame(self, padx=5, pady=5, bg='lightgrey')
        table = tk.Frame(self, padx=5, pady=5, bg='lightgrey')
        top_frame.grid(row=0, column=0, sticky='nsew')
        table.grid(row=1, column=0, sticky='nsew')
        
        title = tk.Label(top_frame, text='Scanner Data', font=tkinter.font.Font(size=10, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, sticky='w')
        # Loop over the dictionary and create labels
        for i, (key, value) in enumerate(self.info.items()):
            label_text = "{}: {}".format(key, value)
            label = tk.Label(top_frame, text=label_text)
            label.grid(row=i+1, column=0, columnspan=2, sticky='w')

        table_title = tk.Label(table, text='RSSI', font=tkinter.font.Font( weight="bold"), relief=tk.RIDGE, width=45)
        table_title.grid(row=0, column=0, sticky="nsew")
        for i, e in enumerate(self.data):
            label = tk.Label(table, text=str(e), relief=tk.RIDGE, width=45)
            label.grid(row=i+1, column=0, sticky="nsew")
    
        # Configure row and column weights to make the cells expand
        for i in range(len(self.data)):
            self.grid_rowconfigure(i, weight=1)

        self.config(bg="white", relief="solid")

class LimitedQueue:
    def __init__(self, max_size):
        self.queue = []
        self.max_size = max_size

    def enqueue(self, item):
        if len(self.queue) >= self.max_size:
            self.queue.pop(0)
        self.queue.append(item)

    def dequeue(self):
        return self.queue.pop(0) if self.queue else None

    def __repr__(self):
        return str(self.queue)


@dataclass
class MockStatusResponse:
    battery_level: int = 0
    clock_status: bool = False
    imu_status: bool = False
    microphone_status: bool = False
    scan_status: bool = False
    pdm_data: list = None
    scan_data: list = None

    def __post_init__(self):
        if self.pdm_data is None:
            self.pdm_data = []
        if self.scan_data is None:
            self.scan_data = []

@dataclass
class MockIMUResponse:
    gyr_x: float = 0.0
    gyr_y: float = 0.0
    gyr_z: float = 0.0
    rot_x: float = 0.0
    rot_y: float = 0.0
    rot_z: float = 0.0
    acc_x: float = 0.0
    acc_y: float = 0.0
    acc_z: float = 0.0
    mag_x: float = 0.0
    mag_y: float = 0.0
    mag_z: float = 0.0

class NewWindow(tk.Toplevel):
    def __init__(self, badge, free_space, name, scan_info, mic_info):
        GET_STATUS_MAIN = False
        tk.Toplevel.__init__(self)
        self.name = name
        self.title("New Window for badge: {}".format(name))
        self.geometry("1500x700")
        self.badge = badge
        self.mic_data = LimitedQueue(10)
        self.scan_data = LimitedQueue(7)
        self.status = MockStatusResponse()  # Initialize with mock status
        self.mic_data.enqueue(self.status.pdm_data)
        self.scan_data.enqueue(self.status.scan_data)
        self.free_space = free_space
        self.imu_status = MockIMUResponse()  # Initialize with mock IMU status
        self.time = 0
        self.scan_info = scan_info
        self.mic_info = mic_info
        self.initUI()
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.async_init())
        self.schedule_update()

    def schedule_update(self):
        """Schedule the next update"""
        self.loop.create_task(self.update_data())
        self.after(5500, self.schedule_update)

    async def update_data(self):
        self.time = self.time + 1
        try:
            status = await self.badge.get_status()
            imu_status = await self.badge.get_imu_data()
            if (status.microphone_status == 0 and status.scan_status == 0 and status.imu_status == 0):
                self.battery.config(text="Available memory: {} MB".format((await self.badge.get_free_sdc_space()).free_space))
        except:
            print('Error with request')
            try:
                await self.badge.connect()
                status = await self.badge.get_status()
                imu_status = await self.badge.get_imu_data()
                if (status.microphone_status == 0 and status.scan_status == 0 and status.imu_status == 0):
                    self.battery.config(text="Available memory: {} MB".format((await self.badge.get_free_sdc_space()).free_space))
            except:
                print('Failed to reconnect')
                return
                
        if status.microphone_status == 0:
            self.MicConfig.data = []
            self.MicConfig.initUI()
        else:
            pdm_data = status.pdm_data
            # update mic
            self.mic_data.enqueue(pdm_data)
            self.MicConfig.data = self.mic_data.queue
            self.MicConfig.initUI()
        if status.scan_status == 0:
            self.ScanConfig.data = []
            self.ScanConfig.initUI()
        else:
            scan_data = status.scan_data
            # update scan
            self.scan_data.enqueue(scan_data)
            self.ScanConfig.data = self.scan_data.queue
            self.ScanConfig.initUI()
        #update imu
        self.IMUConfig.imu_status = imu_status
        self.IMUConfig.time.enqueue(self.time)
        self.IMUConfig.initUI()
        # update circles
        self.MicCircle.update_status(status.microphone_status)
        self.IMUCircle.update_status(status.imu_status)
        self.ScanCircle.update_status(status.scan_status)

    def initUI(self):
        # Create the layout frames
        left_top = tk.Frame(self, padx=5, pady=5)
        right_top = tk.Frame(self, padx=5, pady=5)
        left_down = tk.Frame(self, padx=5, pady=5)
        right_down = tk.Frame(self, padx=5, pady=5)
        left_top.grid(row=0, column=0, sticky='nsew')
        right_top.grid(row=0, column=1, sticky='nsew')
        left_down.grid(row=1, column=0, sticky='nsew')
        right_down.grid(row=1, column=1, sticky='nsew')
        
        # header
        self.badgeId = Label(left_top, text="Badge Id: {}".format(self.name), font=tkinter.font.Font(size=10, ))
        self.badgeId.grid(row=0, column=0, columnspan=2, sticky='w')
        self.midge = Label(left_top, text="Battery: {}%".format(self.status.battery_level), font=tkinter.font.Font(size=10)) 
        self.midge.grid(row=1, column=0, columnspan=2, sticky='w')
        self.battery = Label(left_top, text="Available memory: {}MB".format(self.free_space), font=tkinter.font.Font(size=10))
        self.battery.grid(row=2, column=0, columnspan=2, sticky='w')
        self.reset_battery = Button(left_top, text='Erase', command=self.badge.sdc_errase_all)
        self.reset_battery.grid(row=2, column=1, columnspan=2, sticky='w')

        # IMU
        self.IMULabel = Label(left_top, text="IMU")
        self.IMULabel.grid(row=4, column=0, padx=10, pady=5)
        self.IMUCircle = Circle(left_top, radius=10, status=self.status.imu_status)
        self.IMUCircle.grid(row=4, column=1, padx=10, pady=5)
        self.IMUConfig = IMUConfig(left_top, imu_status=self.imu_status)
        self.IMUConfig.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

        # Scan
        self.ScanLabel = Label(right_top, text="Scanner")
        self.ScanLabel.grid(row=1, column=2, padx=10, pady=5)
        self.ScanCircle = Circle(right_top, radius=10, status=self.status.scan_status)
        self.ScanCircle.grid(row=1, column=3, padx=10, pady=5)
        self.ScanConfig = ScanConfig(right_top, data=self.scan_data.queue, info=self.scan_info)
        self.ScanConfig.grid(row=2, column=2, columnspan=2, padx=10, pady=5)

        # Mic
        self.MicLabel = Label(right_top, text="Microphones")
        self.MicLabel.grid(row=3, column=2, padx=10, pady=5)
        self.MicCircle = Circle(right_top, radius=10, status=self.status.microphone_status)
        self.MicCircle.grid(row=3, column=3, padx=10, pady=5)
        self.MicConfig = MicConfig(right_top, data=self.mic_data.queue, info=self.mic_info)
        self.MicConfig.grid(row=4, column=2, columnspan=2, padx=10, pady=5)

    async def async_init(self):
        try:
            if self.badge:
                self.status = await self.badge.get_status()
                self.free_space = (await self.badge.get_free_sdc_space()).free_space
                self.imu_status = await self.badge.get_imu_data()
                print(self.status)
            else:
                # Use mock data if no badge
                print('badge detected, using mock data')
                self.status = MockStatusResponse()
                self.free_space = 0
                self.imu_status = MockIMUResponse()
        except Exception as e:
            print(f"Error in async_init: {e}")
            # Keep using mock data on error
            self.status = MockStatusResponse()
            self.free_space = 0
            self.imu_status = MockIMUResponse()
        finally:
            # Always update UI
            self.update_ui_with_status()

    def update_ui_with_status(self):
        """Update all UI elements with actual values from status"""
        try:
            self.battery.config(text='Battery: {}%'.format(self.status.battery_level))
            self.IMUCircle.update_status(self.status.imu_status)
            self.MicCircle.update_status(self.status.microphone_status)
            self.ScanCircle.update_status(self.status.scan_status)
        except Exception as e:
            print(f"Error updating UI: {e}")

def get_badges():
    badges = []
    with open('BadgeFramework/mappings2.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            badge = BadgeInterface(row[2])
            badge.connect()
            badges.append({'badge': badge, 'name': row[1], 'address': row[2]})
    return badges
    
class MainApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Lista de dispositivos")
        self.geometry("1100x700")
        self.container_frame = tkinter.ttk.Frame(self)
        self.container_frame.pack(expand=True, fill="both")
        self.custom_components = []
        self.badges = get_badges()

        # Set up asyncio loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        for badge in self.badges:
            custom_component = CustomComponent(self.container_frame, name=badge['name'], badge=badge['badge'], address=badge['address'], gui_instance=self)
            custom_component.pack()
            # Draw a border between custom components
            border = tk.Frame(self.container_frame, bg="gray", height=1)
            border.pack(fill="x")
            self.custom_components.append(custom_component)

        # Schedule asyncio loop to run regularly
        self.after(100, self.run_asyncio_loop)
        self.schedule_update()

    def schedule_update(self):
        """Schedule the next update"""
        self.loop.create_task(self.update_data())
        self.after(1000, self.schedule_update)

    async def update_data(self):
        for badge, custom_component in zip(self.badges, self.custom_components):
            # TODO: fix update data
            badge_status = custom_component.badge_status
            # try:
            #     badge_status = await badge['badge'].get_status()
            # except:
            #     print('Error with request')
            #     try:
            #         await badge['badge'].connect()
            #         badge_status = await badge['badge'].get_status()
            #     except:
            #         print('Failed to reconnect')
            #         continue

            custom_component.badge_status = badge_status
            custom_component.battery['text'] = 'Battery: {}%'.format(badge_status.battery_level)
            custom_component.statusCircle.update_status(badge_status.clock_status)
            custom_component.MicCircle.update_status(badge_status.microphone_status)
            custom_component.IMUCircle.update_status(badge_status.imu_status)
            custom_component.ScanCircle.update_status(badge_status.scan_status)
            
            if (badge_status.microphone_status == 0):
                custom_component.MicStartMonoButton['state'] = 'normal'
                custom_component.MicStartStereoButton['state'] = 'normal'
                custom_component.MicStopButton['state'] = 'disabled'
            else:
                custom_component.MicStartMonoButton['state'] = 'disabled'
                custom_component.MicStartStereoButton['state'] = 'disabled'
                custom_component.MicStopButton['state'] = 'normal'
            
            if (badge_status.imu_status == 0):
                custom_component.IMUStartButton['state'] = 'normal'
                custom_component.IMUStopButton['state'] = 'disabled'
            else:
                custom_component.IMUStartButton['state'] = 'disabled'
                custom_component.IMUStopButton['state'] = 'normal'
            
            if (badge_status.scan_status == 0):
                custom_component.ScanStartButton['state'] = 'normal'
                custom_component.ScanStopButton['state'] = 'disabled'
            else:
                custom_component.ScanStartButton['state'] = 'disabled'
                custom_component.ScanStopButton['state'] = 'normal'

    def run_asyncio_loop(self):
        """Run a single iteration of the asyncio loop"""
        self.loop.call_soon(self.loop.stop)
        self.loop.run_forever()
        self.after(100, self.run_asyncio_loop)

if __name__ == '__main__':
   print('starting app')
   app = MainApp()
   app.mainloop()
