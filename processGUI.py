import threading
import time
import tkinter as tk
import Jetson.GPIO as GPIO
from flow_control import flow_control_thread, flow_lock
from process import flush_process, homogenization_process, sample_process,flush_finish_flag, homogenization_finish_flag, sample_finish_flag
from pump import stop_pump
from config import PUMP_CONFIG, FLOW_CONFIG, PROCESS_CONFIG, shared_data
from logger import setup_logger
import logging

logger = setup_logger(__name__, level=logging.INFO)

class ProcessGUI:
    def __init__(self, root, concentration, chemical):
        self.root = root
        self.concentration = concentration
        self.chemical = chemical
        self.root.title("Process Monitor")

        self.status_label = tk.Label(root, text="Process Status: Waiting...", font=('Helvetica', 16))
        self.status_label.pack(pady=20)

        self.timer_label = tk.Label(root, text="Elapsed Time: 00:00", font=('Arial', 16))
        self.timer_label.pack(pady=10)

        # Timer related variables
        self.start_time = 0
        self.is_timer_running = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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

            shared_data["terminate"] = True
            self.flow_thread.join()  # Wait for the thread to terminate

            self.update_status("Turning off pump...")
            stop_pump(PUMP_CONFIG['pump_bus'])

            self.update_status("All processes completed. Resetting...")
            self.reset_process()

        except Exception as e:
            self.update_status(f"Error: {e}")
        finally:
            GPIO.cleanup()

    def reset_process(self):
        """Resets the process to the initial state."""
        shared_data["flow"] = None
        shared_data["voltage"] = PUMP_CONFIG['initial_voltage']
        shared_data["target_flow"] = PROCESS_CONFIG['flush_rate']
        shared_data["elapsed_time"] = 0
        shared_data["valve_mode"] = "flush_flow"

        self.update_status("Process Status: Waiting...")
        self.root.after(0, lambda: self.timer_label.config(text="Elapsed Time: 00:00"))
        self.root.after(0, self.close_gui)

    def close_gui(self):
        self.root.quit()
        self.root.after(0, self.root.destroy)
        from inputGUI import show_input_window  # Import here to avoid circular import
        show_input_window()

    def on_close(self):
        logger.info("Closing the application...")
        if self.process_thread.is_alive():
            logger.info("Terminating process thread...")
            shared_data["terminate"] = True
            self.process_thread.join(timeout=1)
        GPIO.cleanup()
        self.close_gui()
