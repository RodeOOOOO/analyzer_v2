import time
import logging
from config import PUMP_CONFIG, FLOW_CONFIG, PROCESS_CONFIG, shared_data
from pump import run_sequence
from valve import control_valve_mode
from flow import read_flow, start_flow_measurement, stop_flow_measurement
from smbus2 import SMBus
import threading  # Include threading for the lock

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the lock here
flow_lock = threading.Lock()

def flow_control_thread(pump_bus, flow_bus, shared_data):
    """Thread to monitor flow rate, adjust pump voltage, and control valve mode."""
    logger.debug("Flow control thread initialized.")
    
    if not start_flow_measurement(flow_bus):
        logger.error("Failed to start flow measurement. Exiting.")
        return

    logger.info("Flow measurement started successfully.")

    while True:
        # Check if we should terminate
        if shared_data.get("terminate", False):
            logger.info("Terminating flow control thread.")
            break

        # Monitor the flow rate using flow_bus
        logger.debug("Reading flow...")
        flow = read_flow(flow_bus)
        if flow is not None:
            with flow_lock:
                shared_data["flow"] = flow
        else:
            logger.warning("Failed to read flow measurement.")
            time.sleep(FLOW_CONFIG['sample_interval'])
            continue

        with flow_lock:
            current_flow = shared_data.get("flow", None)
            current_voltage = shared_data.get("voltage", PUMP_CONFIG['initial_voltage'])
            valve_mode = shared_data.get("valve_mode", "flush_flow")
        
        logger.debug(f"Current flow: {current_flow}, Current voltage: {current_voltage}")

        if current_flow is not None:
            target_flow = shared_data.get("target_flow", PROCESS_CONFIG['flush_rate'])
            error = target_flow - current_flow
            deadband = calculate_deadband(FLOW_CONFIG['kp'])

            if abs(error) > deadband:
                kp = FLOW_CONFIG['kp']
                voltage_adjustment = kp * error
                new_voltage = current_voltage + voltage_adjustment
                new_voltage = max(PUMP_CONFIG['min_voltage'], min(PUMP_CONFIG['max_voltage'], new_voltage))

                with flow_lock:
                    shared_data["voltage"] = new_voltage
            else:
                voltage_adjustment = 0.0
                new_voltage = current_voltage

            control_valve_mode(valve_mode)
            logger.info(f"Valve Mode: {valve_mode}, Target Flow Rate: {target_flow:.3f} ml/min, Flow Rate: {current_flow:.3f} ml/min, Voltage: {new_voltage:.1f} V, Adjustment: {voltage_adjustment:.1f} V")
            run_sequence(pump_bus, new_voltage)
        
        time.sleep(FLOW_CONFIG['sample_interval'])

def calculate_deadband(kp, base_kp=FLOW_CONFIG['kp'], base_deadband=FLOW_CONFIG['deadband']):
    """Calculate the deadband based on the proportional control constant (Kp)."""
    return base_deadband * (base_kp / kp)
