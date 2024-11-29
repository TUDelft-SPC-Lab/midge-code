import tkinter as tk
from tkinter import ttk
import asyncio
import pandas as pd
from badge import OpenBadge
from datetime import datetime
# import numpy as np
import sys
import time
import ntplib
# from functools import partial


SENSOR_ALL = 0
SENSOR_MICROPHONE = 1
SENSOR_IMU = 2
SENSOR_SCAN = 3
SENSOR_CHECK_STATUS = 100
SENSOR_TIMEOUT = 15

SENSOR_START = True
SENSOR_STOP = False
CHECK_SYNC = True
CHECK_NO_SYNC = False

BADGES_ALL = -1000
USE_ALL = False  # True to use all badges in .csv file and False to use only marked badges

sensors = ['All', 'Mic', 'IMU', 'Scan']
indicators_long = ['clock', 'microphone', 'imu', 'scan']
indicators_short = ['Clock', 'Mic', 'IMU', 'Scan']
sensor_num = len(indicators_short)


class RedirectText:
    """Class to redirect stdout to a tkinter Text widget."""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.config(state=tk.NORMAL)

    def write(self, string):
        """Redirects the text to the Text widget."""
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)  # Auto-scroll to the bottom
        self.text_widget.update_idletasks()

    def flush(self):
        """Handle flush."""
        pass  # Needed for compatibility with the print function


class BadgeMonitorApp(tk.Tk):
    def __init__(self, ):
        super().__init__()

        self.title("Badge Status Monitor")
        self.badges = pd.read_csv('mappings2.csv')
        # self.badges = []

        # Create a frame to contain the badge area and the terminal area
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")  # Use grid for main_frame

        # Make the window resizable in both directions
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create a canvas to allow scrolling for the badge section
        self.canvas = tk.Canvas(self.main_frame, borderwidth=0)
        self.frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Place the scrollbar and canvas in the window
        self.scrollbar.grid(row=0, column=0, sticky="ns")
        self.canvas.grid(row=0, column=1, sticky="nsew")

        # Bind mouse scroll to canvas
        self.bind_mouse_scroll(self.canvas)

        # Make the badge section expand vertically
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Create a window within the canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # Configure the frame to resize with the canvas
        self.frame.bind("<Configure>", self.on_frame_configure)

        # Terminal on the right
        self.terminal_frame = ttk.Frame(self.main_frame)
        self.terminal_frame.grid(row=0, column=2, sticky="nsew")

        self.terminal_text = tk.Text(self.terminal_frame, wrap="word", state="normal", width=40, height=20)
        self.terminal_text.pack(fill="both", expand=True)

        # Redirect stdout to terminal Text widget
        self.stdout_redirector = RedirectText(self.terminal_text)
        sys.stdout = self.stdout_redirector

        # Set column weights to control space allocation
        self.main_frame.grid_columnconfigure(1, weight=3)  # Badge area
        self.main_frame.grid_columnconfigure(2, weight=1)  # Terminal area

        self.timestamp_labels = {}
        self.sensor_lights = {}
        self.timestamps = {}
        self.update_tasks = {}

        badge_label = ttk.Label(self.frame, text=f"ALL BADGES")
        badge_label.grid(row=0, column=0, padx=80, pady=5)
        check_button = ttk.Button(self.frame, text="Check Status",
                       command=lambda b=BADGES_ALL, s=SENSOR_CHECK_STATUS,
                       m=CHECK_NO_SYNC: self.schedule_async_task(b, s, m))
        check_button.grid(row=0, column=1, padx=20, pady=5)
        for s_idx, sensor in enumerate(sensors):
            s_start_button = ttk.Button(self.frame, text=sensor + " Start", command=
            lambda b=BADGES_ALL, s=s_idx, m=SENSOR_START: self.schedule_async_task(b, s, m))
            s_start_button.grid(row=0, column=2 + 2 * s_idx, padx=5, pady=5)

            s_stop_button = ttk.Button(self.frame, text=sensor + " Stop", command=
            lambda b=BADGES_ALL, s=s_idx, m=SENSOR_STOP: self.schedule_async_task(b, s, m))
            s_stop_button.grid(row=0, column=3 + 2 * s_idx, padx=5, pady=5)

        sync_button = ttk.Button(self.frame, text="Sync",
                                 command=lambda b=BADGES_ALL, s=SENSOR_CHECK_STATUS, m=CHECK_SYNC:
                                 self.schedule_async_task(b, s, m))
        sync_button.grid(row=0, column=10, padx=5, pady=5)

        # Create rows for each badge
        badges_list = list(range(1, len(self.badges) + 5))
        for idx, badge in enumerate(badges_list, start=1):
            row_button, row_status = idx * 2 + 1, idx * 2 + 2
            badge_label = ttk.Label(self.frame, text=f"Badge {badge}")
            badge_label.grid(row=row_button, column=0, padx=80, pady=5)

            check_button = ttk.Button(self.frame, text="Check",
                                      command=lambda b=badge, s=SENSOR_CHECK_STATUS, m=CHECK_NO_SYNC:
                                      self.schedule_async_task(b, s, m))
            check_button.grid(row=row_button, column=1, padx=20, pady=5)

            for s_idx, sensor in enumerate(sensors):
                s_start_button = ttk.Button(self.frame, text=sensor+" Start", command=
                                            lambda b=badge, s=s_idx, m=SENSOR_START: self.schedule_async_task(b, s, m))
                s_start_button.grid(row=row_button, column=2+2*s_idx, padx=5, pady=5)

                s_stop_button = ttk.Button(self.frame, text=sensor+" Stop", command=
                                           lambda b=badge, s=s_idx, m=SENSOR_STOP: self.schedule_async_task(b, s, m))
                s_stop_button.grid(row=row_button, column=3+2*s_idx, padx=5, pady=5)

            sync_button = ttk.Button(self.frame, text="Sync",
                                     command=lambda b=badge, s=SENSOR_CHECK_STATUS, m=CHECK_SYNC:
                                     self.schedule_async_task(b, s, m))
            sync_button.grid(row=row_button, column=10, padx=5, pady=5)

            sensor_light_canvases = []
            for s_idx, sensor in enumerate(indicators_short, start=1):
                sensor_light_canvas = tk.Canvas(self.frame, width=20, height=20)
                sensor_light_canvas.grid(row=row_status, column=1+2*s_idx, padx=5, pady=5)
                sensor_light = sensor_light_canvas.create_oval(5, 5, 15, 15, fill="red")
                sensor_light_canvases.append((sensor_light_canvas, sensor_light))

                sensor_label = ttk.Label(self.frame, text=sensor + ' status:')
                sensor_label.grid(row=row_status, column=2*s_idx, padx=5, pady=5)

            # Create a label to display the last updated time and elapsed time
            timestamp_label = ttk.Label(self.frame, text="Last updated: N/A")
            timestamp_label.grid(row=row_status, column=0, padx=5, pady=5)

            # Create a label to display the elapsed time in seconds
            elapsed_time_label = ttk.Label(self.frame, text="Elapsed: N/A")
            elapsed_time_label.grid(row=row_status, column=1, padx=5, pady=5)

            # Store the canvas, light, sensor lights, timestamp label, and elapsed time label
            self.timestamp_labels[badge] = (timestamp_label, elapsed_time_label)
            self.sensor_lights[badge] = sensor_light_canvases

    def bind_mouse_scroll(self, widget):
        """Bind the mouse scroll event to the canvas."""
        # Windows OS uses "<MouseWheel>", others use "<Button-4>" and "<Button-5>"
        widget.bind_all("<MouseWheel>", self.on_mouse_wheel)
        widget.bind_all("<Button-4>", self.on_mouse_wheel)
        widget.bind_all("<Button-5>", self.on_mouse_wheel)

    def on_mouse_wheel(self, event):
        """Handle the mouse scroll event."""
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.canvas.yview_scroll(1, "units")

    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def schedule_async_task(self, badge_id, sensor_idx, mode: bool):
        if badge_id == BADGES_ALL:
            asyncio.create_task(self.async_task_all_badges(sensor_idx, mode, use_all=USE_ALL))
        else:
            asyncio.create_task(self.async_task_sensors(badge_id, sensor_idx, mode))

    async def async_task_all_badges(self, sensor_idx, mode: bool, use_all: bool):
        # await self.async_task_sensors(badge_id=1, sensor_idx=sensor_idx, mode=mode)
        for row_id in self.badges.index:
            badge_id, use_flag = int(self.badges['Participant Id'][row_id]), bool(self.badges['Use'][row_id])
            if use_flag or use_all:
                await self.async_task_sensors(badge_id=badge_id, sensor_idx=sensor_idx, mode=mode)

    async def async_task_sensors(self, badge_id: int, sensor_idx: int, mode: bool):
        if sensor_idx == SENSOR_MICROPHONE:
            await self.async_sensor(badge_id=badge_id, mode=mode, sensor_name='microphone')
        elif sensor_idx == SENSOR_IMU:
            await self.async_sensor(badge_id=badge_id, mode=mode, sensor_name='imu')
        elif sensor_idx == SENSOR_SCAN:
            await self.async_sensor(badge_id=badge_id, mode=mode, sensor_name='scan')
        elif sensor_idx == SENSOR_ALL:
            await self.async_sensor(badge_id=badge_id, mode=mode, sensor_name='microphone')
            await self.async_sensor(badge_id=badge_id, mode=mode, sensor_name='imu')
            await self.async_sensor(badge_id=badge_id, mode=mode, sensor_name='scan')

        if sensor_idx == SENSOR_CHECK_STATUS:
            await self.async_check_status(badge_id, mode=mode)
        else:
            await self.async_check_status(badge_id, mode=CHECK_NO_SYNC)

    async def async_check_status(self, badge_id, mode=CHECK_NO_SYNC):
        # Call the async function to check the status
        # statuses, timestamp = await self.check_status(badge_id)
        statuses, timestamp = await self.async_sensor(badge_id=badge_id, mode=mode, sensor_name='status')
        if statuses is None:
            return
        sensor_statuses = [getattr(statuses, s + '_status') for s in indicators_long]

        # Get the canvas and light object for the badge
        timestamp_label, elapsed_time_label = self.timestamp_labels[badge_id]

        sensor_light_canvases = self.sensor_lights[badge_id]
        for sensor_idx, (sensor_light_canvas, sensor_light) in enumerate(sensor_light_canvases):
            sensor_color = "green" if sensor_statuses[sensor_idx] == 1 else "red"
            sensor_light_canvas.itemconfig(sensor_light, fill=sensor_color)

        # Format the timestamp and update the timestamp label
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_label.config(text=f"Last updated: {formatted_time}")

        # Update the timestamps dictionary with the current time
        self.timestamps[badge_id] = timestamp

        # Cancel the previous update task if it exists
        if badge_id in self.update_tasks:
            self.update_tasks[badge_id].cancel()

        # Start a new task to update the elapsed time
        task = asyncio.create_task(self.update_elapsed_time(badge_id, elapsed_time_label, timestamp))
        self.update_tasks[badge_id] = task

    @staticmethod
    def get_operation_name(mode_name: str, sensor_name: str) -> str:
        if sensor_name in indicators_long:
            return f'{mode_name}_{sensor_name}'
        elif sensor_name == 'status':
            return 'get_status'
        elif sensor_name == 'sdc_space':
            return 'get_free_sdc_space'
        else:
            raise ValueError

    async def async_sensor(self, badge_id, sensor_name, mode: bool):
        # badge_addr = self.get_badge_address(badge_id)
        mode_name = 'start' if mode == SENSOR_START else 'stop'
        op_name = self.get_operation_name(mode_name, sensor_name)
        badge_op_desc = f'Badge {badge_id} {op_name}'
        print(f"Executing: {badge_op_desc}...")

        try:
            # await asyncio.wait_for(self.eternity(), timeout=1.0)
            response = await asyncio.wait_for(self.async_sensor_operation(badge_id, op_name, mode),
                                              timeout=SENSOR_TIMEOUT)
            print(f'Info: {badge_op_desc} successfully.')
        except asyncio.TimeoutError:
            print(f"Warning: {badge_op_desc} has timed out! (>{SENSOR_TIMEOUT}s)")
            response = None
        except Exception as e:
            print(e)
            response = None

        # await asyncio.sleep(1)  # Simulate delay
        timestamp = datetime.now()  # Get the current timestamp
        return response, timestamp

    async def async_sensor_operation(self, badge_id, op_name, mode):
        badge_addr = self.get_badge_address(badge_id)
        async with OpenBadge(badge_id, badge_addr) as open_badge:
            sensor_operation = getattr(open_badge, op_name)
            if op_name == 'get_status' and mode == CHECK_SYNC:
                return_message = await sensor_operation(t=datetime.now().timestamp())
            else:
                return_message = await sensor_operation()
            # print(return_message)
        return return_message

    def get_badge_address(self, badge_id: int) -> str:
        badge = self.badges[self.badges['Participant Id'] == badge_id]
        address = badge['Mac Address'].to_numpy()[0]  # There should be a more elegant way to do this
        return address

    @staticmethod
    async def update_elapsed_time(badge_id, elapsed_time_label, last_update_time):
        """Continuously update the elapsed time since the last status update."""
        try:
            while True:
                await asyncio.sleep(1)  # Update every second
                now = datetime.now()
                elapsed_seconds = (now - last_update_time).total_seconds()
                elapsed_time_label.config(text=f"Elapsed: {int(elapsed_seconds)}s")
        except asyncio.CancelledError:
            pass  # Task was cancelled

    def run(self):
        # Start the tkinter mainloop
        self.mainloop()


# Main function that starts the tkinter app and runs the event loop
def run_tkinter_async():
    app = BadgeMonitorApp()

    async def main_loop():
        while True:
            await asyncio.sleep(0.01)  # Non-blocking sleep to allow tkinter to update
            app.update_idletasks()
            app.update()

    # Schedule the main loop in asyncio
    asyncio.run(main_loop())


# def get_ntp_time(ntp_server='pool.ntp.org'):
#     # Create an NTP client
#     client = ntplib.NTPClient()
#
#     try:
#         # Query the NTP server
#         response = client.request(ntp_server)
#
#         # Convert the response to datetime
#         ntp_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
#         print("NTP time:", ntp_time.strftime('%Y-%m-%d %H:%M:%S %Z'))
#         return ntp_time
#
#     except Exception as e:
#         print("Could not connect to NTP server:", e)
#         return None


# Use a local NTP server (replace with your server IP if needed)
# ntp_server_ip = '192.168.1.100'  # Example IP for a local NTP server
# ntp_time = get_ntp_time(ntp_server=ntp_server_ip)


if __name__ == "__main__":
    run_tkinter_async()