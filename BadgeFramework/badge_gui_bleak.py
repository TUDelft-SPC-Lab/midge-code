import tkinter as tk
from tkinter import ttk
import asyncio
import pandas as pd
from badge import OpenBadge
from datetime import datetime
import numpy as np
import sys
from functools import partial


SENSOR_ALL = 0
SENSOR_MICROPHONE = 1
SENSOR_IMU = 2
SENSOR_SCAN = 3
SENSOR_CHECK_STATUS = 100

SENSOR_START = True
SENSOR_STOP = False

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
    def __init__(self, badges):
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

        # Create rows for each badge
        for idx, badge in enumerate(badges, start=1):
            row_button, row_status = idx * 2 - 1, idx * 2
            badge_label = ttk.Label(self.frame, text=f"Badge {badge}")
            badge_label.grid(row=row_button, column=0, padx=80, pady=5)

            check_button = ttk.Button(self.frame, text="Check Status",
                                      command=lambda b=badge, s=100, m=1: self.schedule_async_task(b, s, m))
            check_button.grid(row=row_button, column=1, padx=20, pady=5)

            for s_idx, sensor in enumerate(sensors):
                s_start_button = ttk.Button(self.frame, text=sensor+" Start", command=
                                            lambda b=badge, s=s_idx, m=SENSOR_START: self.schedule_async_task(b, s, m))
                s_start_button.grid(row=row_button, column=2+2*s_idx, padx=5, pady=5)

                s_stop_button = ttk.Button(self.frame, text=sensor+" Stop", command=
                                           lambda b=badge, s=s_idx, m=SENSOR_STOP: self.schedule_async_task(b, s, m))
                s_stop_button.grid(row=row_button, column=3+2*s_idx, padx=5, pady=5)

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
        # Schedule the coroutine to run asynchronously
        async_sensor = partial(self.async_sensor_operation, badge_id=badge_id, mode=mode)
        if sensor_idx == SENSOR_CHECK_STATUS:
            asyncio.create_task(self.async_check_status(badge_id))
        elif sensor_idx == SENSOR_MICROPHONE:
            asyncio.create_task(async_sensor(sensor_name='microphone'))
        elif sensor_idx == SENSOR_IMU:
            asyncio.create_task(async_sensor(sensor_name='imu'))
        elif sensor_idx == SENSOR_SCAN:
            asyncio.create_task(async_sensor(sensor_name='scan'))
        elif sensor_idx == SENSOR_ALL:
            asyncio.create_task(async_sensor(sensor_name='microphone'))
            asyncio.create_task(async_sensor(sensor_name='imu'))
            asyncio.create_task(async_sensor(sensor_name='scan'))

    async def async_check_status(self, badge_id):
        # Call the async function to check the status
        statuses, timestamp = await self.check_status(badge_id)
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

    async def check_status(self, badge_id):
        badge_addr = self.get_badge_address(badge_id)
        print(f"Checking status for badge {badge_id}...")

        # simulate
        # await asyncio.sle(2)  # Simulate delay
        # statuses = np.random.randint(2, size=sensor_num)

        # real status
        async with OpenBadge(badge_id, badge_addr) as open_badge:
            statuses = await open_badge.get_status()

        timestamp = datetime.now()  # Get the current timestamp
        print(statuses)
        print(f"Check status for badge {badge_id} completed.")
        return statuses, timestamp

    async def async_sensor_operation(self, badge_id, sensor_name, mode: bool):
        badge_addr = self.get_badge_address(badge_id)
        mode_name = 'start' if mode == SENSOR_START else 'stop'
        op_name = f'{mode_name}_{sensor_name}'
        print(f"Executing: {mode_name} {sensor_name} for badge {badge_id}...")
        async with OpenBadge(badge_id, badge_addr) as open_badge:
            sensor_operation = getattr(open_badge, op_name)
            return_message = await sensor_operation()
            print(return_message)
        # await asyncio.sleep(1)  # Simulate delay
        timestamp = datetime.now()  # Get the current timestamp
        print(f'Badge {badge_id} {sensor_name} {mode_name} successfully.')
        return timestamp

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
    badges = list(range(1, 50))  # Badge numbers from 1 to 10
    app = BadgeMonitorApp(badges)

    async def main_loop():
        while True:
            await asyncio.sleep(0.01)  # Non-blocking sleep to allow tkinter to update
            app.update_idletasks()
            app.update()

    # Schedule the main loop in asyncio
    asyncio.run(main_loop())


if __name__ == "__main__":
    run_tkinter_async()