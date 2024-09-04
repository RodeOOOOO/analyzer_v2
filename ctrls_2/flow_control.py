import time
import logging
from config import PUMP_CONFIG, FLOW_CONFIG, PROCESS_CONFIG, calculate_deadband
from pump import run_sequence
from valve import control_valve_mode
from flow import read_flow, start_flow_measurement, stop_flow_measurement
from smbus2 import SMBus

# Initialize logging
logger = logging.getLogger(__name__)

def flow_control_thread(pump_bus, flow_bus, shared_data, flow_lock):
    """Thread to monitor flow rate, adjust pump voltage, and control valve mode."""
    logger.debug("Flow control thread initialized.")
    
    if not start_flow_measurement(flow_bus):
        logger.error("Failed to start flow measurement. Exiting.")
        return

    logger.info("Flow measurement started successfully.")

    while True:
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
            current_voltage = shared_data.get("voltage", PUMP_CONFIG['initial_voltage'])  # Start at 0 if not set
            valve_mode = shared_data.get("valve_mode", "flush_flow")  # Get current valve mode
        
        logger.debug(f"Current flow: {current_flow}, Current voltage: {current_voltage}")

        if current_flow is not None:
            # Access the target flow rate from PROCESS_CONFIG
            target_flow = shared_data.get("target_flow", PROCESS_CONFIG['flush_rate'])  # Default to flush_rate if not set
            
            # Calculate the error
            error = target_flow - current_flow
            
            # Calculate the deadband based on the current kp
            deadband = calculate_deadband(FLOW_CONFIG['kp'])
            
            # Determine if an adjustment is needed
            if abs(error) > deadband:
                # Adjust the voltage if the error is outside the deadband
                kp = FLOW_CONFIG['kp']
                voltage_adjustment = kp * error
                new_voltage = current_voltage + voltage_adjustment

                # Ensure voltage is within the allowed range
                new_voltage = max(PUMP_CONFIG['min_voltage'],
                                  min(PUMP_CONFIG['max_voltage'], new_voltage))

                # Update shared_data with the new voltage
                with flow_lock:
                    shared_data["voltage"] = new_voltage
            else:
                voltage_adjustment = 0.0
                new_voltage = current_voltage

            # Check and control the valve mode
            control_valve_mode(valve_mode)

            # Log the valve mode, target flow, current flow, voltage, and adjustment
            logger.info(f"Valve Mode: {valve_mode}, "
                        f"Target Flow Rate: {target_flow:.3f} ml/min, "
                        f"Flow Rate: {current_flow:.3f} ml/min, "
                        f"Voltage: {new_voltage:.1f} V, "
                        f"Adjustment: {voltage_adjustment:.1f} V")

            # Adjust the pump voltage if needed using pump_bus
            run_sequence(pump_bus, new_voltage)
        
        # Reduce sleep time for faster updates
        time.sleep(FLOW_CONFIG['sample_interval'])  # Keep in sync with flow sampling
