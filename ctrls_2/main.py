import time
import logging
from smbus2 import SMBus
from config import PUMP_CONFIG, FLOW_CONFIG, calculate_deadband
from pump import run_sequence
from flow import read_flow, start_flow_measurement, stop_flow_measurement  # Updated import
import threading

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared container for flow and voltage
shared_data = {"flow": None, "voltage": PUMP_CONFIG['initial_voltage']}
flow_lock = threading.Lock()

def adjust_pump_voltage(bus, shared_data, flow_lock):
    """Adjust the pump voltage to maintain the target flush rate, with deadband consideration."""
    while True:
        with flow_lock:
            current_flow = shared_data.get("flow", None)
            current_voltage = shared_data.get("voltage", PUMP_CONFIG['initial_voltage'])  # Start at 0 if not set
        
        if current_flow is not None:
            target_flow = PUMP_CONFIG['flush_rate']
            
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

            # Log the target flow, current flow, voltage, and adjustment
            logger.info(f"Target Flow Rate: {target_flow:.3f} ml/min, "
                        f"Flow Rate: {current_flow:.3f} ml/min, "
                        f"Voltage: {new_voltage:.1f} V, "
                        f"Adjustment: {voltage_adjustment:.1f} V")
            
            # Adjust the pump voltage if needed
            run_sequence(bus, new_voltage)
        
        # Reduce sleep time for faster updates
        time.sleep(FLOW_CONFIG['sample_interval'])  # Keep in sync with flow sampling

def monitor_flow_sensor(bus, shared_data, flow_lock):
    """Continuously monitor the flow rate and store it in shared_data."""
    if start_flow_measurement(bus):
        logger.info("Flow measurement started successfully.")
        while True:
            flow = read_flow(bus)
            if flow is not None:
                with flow_lock:
                    shared_data["flow"] = flow
            else:
                logger.warning("Failed to read flow measurement.")
            time.sleep(FLOW_CONFIG['sample_interval'])  # Pause between readings
    else:
        logger.error("Failed to start flow measurement. Exiting.")

def main():
    # Open I2C bus
    with SMBus(PUMP_CONFIG['pump_bus']) as pump_bus, SMBus(FLOW_CONFIG['flow_bus']) as flow_bus:
        # Start flow monitoring in a separate thread
        flow_thread = threading.Thread(target=monitor_flow_sensor, args=(flow_bus, shared_data, flow_lock))
        flow_thread.start()

        # Start adjusting the pump voltage based on the flow rate
        adjust_pump_voltage(pump_bus, shared_data, flow_lock)

if __name__ == "__main__":
    main()
