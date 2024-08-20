import threading
import tkinter as tk
from tkinter import ttk
import logging
import time
from smbus2 import SMBus
from flow_sensor import read_flow, start_flow_measurement, stop_flow_measurement
from pump_control import run_sequence, stop_pump
from config import PUMP_CONTROL_CONFIG, FLOW_SENSOR_CONFIG, calculate_deadband
from vna_module import run_vna_sweep  # Import only the VNA sweep function

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def validate_flow_and_start_sweep(shared_data, concentration, chemical, gui_restart_flag):
    logger.info("Validating flow rate before starting sweep...")
    start_time = time.time()
    try:
        with SMBus(1) as flow_bus, SMBus(7) as pump_bus:
            while time.time() - start_time < FLOW_SENSOR_CONFIG['run_duration']:
                logger.debug("Entering adaptive flow control loop.")

                # Read flow value
                flow_value = read_flow(flow_bus)
                if flow_value is None:
                    logger.warning("Flow reading failed, defaulting to 0.0 ml/min.")
                    flow_value = 0.0

                shared_data['flow_value'] = flow_value
                logger.debug(f"Current flow value: {flow_value:.3f} ml/min")

                # Dynamically calculate deadband based on the current Kp
                current_deadband = calculate_deadband(FLOW_SENSOR_CONFIG['kp'])
                logger.debug(f"Calculated deadband: {current_deadband:.3f}")

                # Calculate error and adjust voltage
                error = FLOW_SENSOR_CONFIG['target_flow_rate'] - flow_value
                logger.debug(f"Calculated error: {error:.3f} ml/min from target flow rate.")

                if abs(error) > current_deadband:
                    adjustment = FLOW_SENSOR_CONFIG['kp'] * error
                    shared_data['voltage'] = max(
                        PUMP_CONTROL_CONFIG['min_voltage'],
                        min(PUMP_CONTROL_CONFIG['max_voltage'],
                            shared_data['voltage'] + adjustment))
                    
                    logger.debug(f"Adjusting voltage by {adjustment:.3f} V. New voltage: {shared_data['voltage']} V")
                    run_sequence(pump_bus, shared_data['voltage'])
                else:
                    logger.debug(f"Error within deadband, no voltage adjustment needed.")

                logger.info(f"Flow Value: {flow_value:.3f} ml/min, Adjusted Voltage: {shared_data['voltage']} V")

                if abs(error) <= current_deadband:
                    logger.info("Flow rate validated. Starting VNA sweep...")
                    vna_thread = threading.Thread(target=run_vna_sweep, args=(concentration, chemical))
                    vna_thread.start()
                    break

                time.sleep(FLOW_SENSOR_CONFIG['sample_interval'])

            # Continue printing flow and voltage until the VNA sweep is done
            while vna_thread.is_alive():
                flow_value = read_flow(flow_bus)
                if flow_value is None:
                    flow_value = 0.0
                shared_data['flow_value'] = flow_value
                logger.info(f"Flow Value: {flow_value:.3f} ml/min, Current Voltage: {shared_data['voltage']} V")
                time.sleep(FLOW_SENSOR_CONFIG['sample_interval'])

            # After VNA sweep is done, stop the pump
            logger.info("VNA sweep complete. Turning off the pump.")
            stop_pump(pump_bus)

            # Signal to restart the GUI on the main thread
            gui_restart_flag.set()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        stop_pump(pump_bus)
        gui_restart_flag.set()

def on_submit():
    concentration = concentration_var.get()
    chemical = chemical_var.get()
    if concentration and chemical:
        shared_data = {
            'flow_value': 0.0,
            'voltage': PUMP_CONTROL_CONFIG['homogenization_voltage']
        }
        gui_restart_flag = threading.Event()  # Flag to signal GUI restart

        # Start the process in a new thread
        threading.Thread(target=run_homogenization_and_validate_flow, args=(shared_data, concentration, chemical, gui_restart_flag)).start()

        root.destroy()  # Close the Tkinter window after submission

        # Wait for the flag to restart the GUI
        gui_restart_flag.wait()
        start_gui()

    else:
        logger.error("Please enter a concentration and select a chemical.")

def run_homogenization_and_validate_flow(shared_data, concentration, chemical, gui_restart_flag):
    try:
        with SMBus(1) as flow_bus, SMBus(7) as pump_bus:
            if start_flow_measurement(flow_bus):
                logger.info(f"Running pump at homogenization voltage: {PUMP_CONTROL_CONFIG['homogenization_voltage']} V")
                run_sequence(pump_bus, PUMP_CONTROL_CONFIG['homogenization_voltage'])
                time.sleep(PUMP_CONTROL_CONFIG['homogenization_duration'])
                shared_data['voltage'] = PUMP_CONTROL_CONFIG['homogenization_voltage']

                validate_flow_and_start_sweep(shared_data, concentration, chemical, gui_restart_flag)
                
                while threading.active_count() > 1:
                    time.sleep(1)

                stop_flow_measurement(flow_bus)
                stop_pump(pump_bus)
                logger.info("Process complete. Ready for next sweep.")
            else:
                logger.error("Failed to start flow measurement.")
                gui_restart_flag.set()
    except Exception as e:
        logger.error(f"An unexpected error occurred during homogenization and validation: {e}")
        gui_restart_flag.set()

def start_gui():
    global root
    root = tk.Tk()
    root.title("VNA Sweep Configuration")

    tk.Label(root, text="Enter Concentration (ppm):").grid(row=0, column=0, padx=10, pady=10)
    global concentration_var
    concentration_var = tk.StringVar()
    tk.Entry(root, textvariable=concentration_var).grid(row=0, column=1, padx=10, pady=10)

    tk.Label(root, text="Select Chemical:").grid(row=1, column=0, padx=10, pady=10)
    global chemical_var
    chemical_var = tk.StringVar()
    chemicals = ["PFOA", "PFOS", "PFBS", "PFNA"]  # Add more chemicals as needed
    chemical_dropdown = ttk.Combobox(root, textvariable=chemical_var, values=chemicals)
    chemical_dropdown.grid(row=1, column=1, padx=10, pady=10)
    chemical_dropdown.current(0)  # Set default selection

    submit_button = tk.Button(root, text="Start Sweep", command=on_submit)
    submit_button.grid(row=2, column=0, columnspan=2, pady=20)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
