import threading
import logging
import time
import tkinter as tk
from tkinter import ttk
import Jetson.GPIO as GPIO
from flow_control import flow_control_thread, flow_lock
from process import flush_process, homogenization_process, sample_process, flush_finish_flag, homogenization_finish_flag, sample_finish_flag
from pump import stop_pump
from config import PUMP_CONFIG, FLOW_CONFIG, PROCESS_CONFIG, shared_data

# Initialize logger
logger = logging.getLogger(__name__)

class CombinedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VNA Sweep and Process Monitor")
        
        # Set reduced window size for better proportion
        window_width = 600
        window_height = 400
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position to center the window
        position_right = int(screen_width/2 - window_width/2)
        position_down = int(screen_height/2 - window_height/2)
        
        # Set window geometry and center it
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_down}")

        # Set dark mode colors
        self.bg_color = "#1e1e1e"  # Background color
        self.fg_color = "#ffffff"  # Text color
        self.entry_bg = "#333333"  # Entry background
        self.button_bg = "#444444"  # Button background
        self.button_fg = "#ffffff"  # Button text color

        # Apply background color
        self.root.configure(bg=self.bg_color)

        # Create grid layout for centering
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(7, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # User input section (centered in grid)
        self.concentration_var = tk.StringVar()
        self.chemical_var = tk.StringVar()

        tk.Label(root, text="Enter Concentration (ppm):", font=('Arial', 14), bg=self.bg_color, fg=self.fg_color).grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        tk.Entry(root, textvariable=self.concentration_var, bg=self.entry_bg, fg=self.fg_color, font=('Arial', 14)).grid(row=1, column=2, padx=10, pady=10, sticky='ew')

        tk.Label(root, text="Select Chemical:", font=('Arial', 14), bg=self.bg_color, fg=self.fg_color).grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        chemicals = ["PFOA", "PFOS", "PFBS", "PFNA"]
        self.chemical_dropdown = ttk.Combobox(root, textvariable=self.chemical_var, values=chemicals, font=('Arial', 14), width=10)
        self.chemical_dropdown.grid(row=2, column=2, padx=10, pady=10, sticky='ew')
        self.chemical_dropdown.current(0)

        submit_button = tk.Button(root, text="Start Sweep", command=self.on_submit, bg=self.button_bg, fg=self.button_fg, font=('Arial', 14))
        submit_button.grid(row=3, column=1, columnspan=2, pady=20)

        # Process monitoring section (centered in grid)
        self.status_label = tk.Label(root, text="Process Status: Waiting...", font=('Arial', 16), bg=self.bg_color, fg=self.fg_color)
        self.status_label.grid(row=4, column=1, columnspan=2, pady=20)

        self.timer_label = tk.Label(root, text="Elapsed Time: 00:00", font=('Arial', 16), bg=self.bg_color, fg=self.fg_color)
        self.timer_label.grid(row=5, column=1, columnspan=2, pady=10)

        # Timer related variables
        self.start_time = 0
        self.is_timer_running = False
        self.concentration = None
        self.chemical = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_submit(self):
        """Handle the submit button click, capture inputs, and start the process."""
        self.concentration = self.concentration_var.get()
        self.chemical = self.chemical_var.get()

        if self.concentration and self.chemical:
            self.start_process()

    def start_process(self):
        """Start the process sequence with the user inputs."""
        self.process_thread = threading.Thread(target=self.run_process_sequence)
        self.process_thread.start()

    def update_status(self, message):
        """Update the process status on the GUI."""
        self.root.after(0, lambda: self.status_label.config(text=message))

    def start_timer(self):
        """Start the timer and update the GUI every second."""
        self.start_time = time.time()
        self.is_timer_running = True
        self.update_timer()

    def stop_timer(self):
        """Stop the timer."""
        self.is_timer_running = False

    def update_timer(self):
        """Update the timer label on the GUI."""
        if self.is_timer_running:
            elapsed_time = int(time.time() - self.start_time)
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            self.root.after(0, lambda: self.timer_label.config(text=f"Elapsed Time: {minutes:02}:{seconds:02}"))
            self.root.after(1000, self.update_timer)

    def run_process_sequence(self):
        """Runs the process sequence and updates the GUI."""
        GPIO.setmode(GPIO.BOARD)
        try:
            self.flow_thread = threading.Thread(target=flow_control_thread, args=(PUMP_CONFIG['pump_bus'], FLOW_CONFIG['flow_bus'], shared_data))
            self.flow_thread.start()

            # Flush process
            self.update_status("Starting flush process...")
            self.start_timer()
            flush_process(shared_data, flow_lock, flush_finish_flag)
            self.stop_timer()

            # Homogenization process
            self.update_status("Starting homogenization process...")
            self.start_timer()
            homogenization_process(shared_data, flow_lock, homogenization_finish_flag)
            self.stop_timer()

            # Sample process
            self.update_status(f"Starting sample process for {self.concentration}ppm {self.chemical}...")
            self.start_timer()
            sample_process(shared_data, flow_lock, sample_finish_flag, self.concentration, self.chemical)
            self.stop_timer()

            # Final flush process
            self.update_status("Starting final flush process...")
            self.start_timer()
            flush_process(shared_data, flow_lock, flush_finish_flag)
            self.stop_timer()

            # Terminate the flow control thread
            shared_data["terminate"] = True
            self.flow_thread.join()  # Wait for the thread to terminate

            # Turn off the pump
            self.update_status("Turning off pump...")
            stop_pump(PUMP_CONFIG['pump_bus'])

            self.update_status("All processes completed. Resetting...")

            self.reset_process()

        except Exception as e:
            self.update_status(f"Error: {e}")
        finally:
            #GPIO.cleanup()
            print('process complete')

    def reset_process(self):
        """Resets the process to the initial state."""
        shared_data["flow"] = None
        shared_data["voltage"] = PUMP_CONFIG['initial_voltage']
        shared_data["target_flow"] = PROCESS_CONFIG['flush_rate']
        shared_data["elapsed_time"] = 0
        shared_data["valve_mode"] = "flush_flow"
        shared_data["terminate"] = False 

        self.update_status("Process Status: Waiting...")
        self.root.after(0, lambda: self.timer_label.config(text="Elapsed Time: 00:00"))

    def on_close(self):
        logger.info("Closing the application...")
        if self.process_thread.is_alive():
            logger.info("Terminating process thread...")
            shared_data["terminate"] = True
            self.process_thread.join(timeout=1)
        # Only clean GPIO on program exit
        GPIO.cleanup()
        self.root.quit()
        self.root.destroy()


def show_combined_window():
    root = tk.Tk()
    app = CombinedGUI(root)
    root.mainloop()

if __name__ == "__main__":
    show_combined_window()
