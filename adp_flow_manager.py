import threading
from smbus2 import SMBus, i2c_msg
import time
import logging
import os
import csv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for the flow sensor
I2C_SLF3S_ADDRESS = 0x08
SCALE_FACTOR_FLOW = 10000.0
calibration_cmdByte = 0x08

# Constants for the pump driver
PUMP_I2C_ADDRESS = 0x59
REGISTER_PAGE_FF = 0xFF

# Target flow rate in ml/min
TARGET_FLOW_RATE = 0.4

# Initial desired voltage
INITIAL_VOLTAGE = 53
MAX_VOLTAGE = 150  # Maximum allowed voltage
MIN_VOLTAGE = 0  # Minimum allowed voltage

# Control parameters
Kp = 5  # Reduced proportional control constant
deadband = 0.01  # Deadband around the target flow rate

# Control data for the pump
CONTROL_DATA = [0x00, 0x3B, 0x01, 0x01]

# Duration to run the process (in seconds)
RUN_DURATION = 900

# Sampling interval (in seconds)
SAMPLE_INTERVAL = 0.5

# Shared container for voltage
voltage_container = {'current_voltage': INITIAL_VOLTAGE}

def start_flow_measurement(bus):
    logger.info("Starting continuous measurement...")
    try:
        bus.write_i2c_block_data(I2C_SLF3S_ADDRESS, 0x36, [calibration_cmdByte], force=True)
    except OSError as e:
        logger.error(f"Error starting continuous measurement: {e}")
        return False
    return True

def stop_flow_measurement(bus):
    logger.info("Stopping continuous measurement...")
    try:
        bus.write_i2c_block_data(I2C_SLF3S_ADDRESS, 0x3F, [0xF9], force=True)
    except OSError as e:
        logger.error(f"Error stopping continuous measurement: {e}")

def read_flow(bus):
    try:
        msg = i2c_msg.read(I2C_SLF3S_ADDRESS, 3)
        bus.i2c_rdwr(msg)
    except OSError as e:
        logger.error(f"Error reading from sensor: {e}")
        return None
    
    data = list(msg)
    sensor_flow_value = (data[0] << 8) | data[1]
    
    signed_flow_value = int.from_bytes(sensor_flow_value.to_bytes(2, byteorder='big'), byteorder='big', signed=True)
    scaled_flow_value = float(signed_flow_value) / SCALE_FACTOR_FLOW
    
    return scaled_flow_value

def write_waveform_data(bus, address, register_page_ff, voltage):
    amplitude_value = int((voltage / 150.0) * 255)
    
    waveform_data = [
        0x05, 0x80, 0x06, 0x00, 0x09, 0x00, 
        amplitude_value, 0x0C, 0x64, 0x00
    ]
    
    logger.debug(f"Setting pump voltage to {voltage}V (amplitude value: {amplitude_value})")

    bus.write_i2c_block_data(address, register_page_ff, [1])
    logger.debug("Switched to page 1")
    
    for i, data in enumerate(waveform_data):
        bus.write_i2c_block_data(address, i, [data])
        logger.debug(f"Written to register 0x{i:02X} on page 1: {data}")
    
    time.sleep(0.2)

def write_control_data(bus, address, register_page_ff, control_data):
    bus.write_i2c_block_data(address, register_page_ff, [0])
    logger.debug("Switched to page 0")
    
    for i, data in enumerate(control_data):
        bus.write_i2c_block_data(address, i, [data])
        logger.debug(f"Written to register 0x{i:02X} on page 0: {data}")
    
    time.sleep(0.2)

def run_sequence(bus, voltage):
    logger.debug(f"Running sequence with voltage: {voltage}")
    write_waveform_data(bus, PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, voltage)
    write_control_data(bus, PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, CONTROL_DATA)
    bus.write_i2c_block_data(PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, [0])
    logger.debug("Switched back to page 0 after sequence")

def stop_pump(bus):
    zero_waveform_data = [0x05, 0x80, 0x06, 0x00, 0x09, 0x00, 0x00, 0x0C, 0x64, 0x00]
    write_waveform_data(bus, PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, 0)
    logger.info("Pump voltage set to 0.")

def flow_sensor_thread(adjustment_event, voltage_container):
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{data_dir}/{RUN_DURATION}_s_{INITIAL_VOLTAGE}V_adp_v_{TARGET_FLOW_RATE}_ml_min_{timestamp}.csv"
    
    with SMBus(1) as flow_bus, open(file_name, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'flow_value', 'voltage']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        time.sleep(1)
        if start_flow_measurement(flow_bus):
            try:
                start_time = time.time()
                while time.time() - start_time < RUN_DURATION:
                    flow_value = read_flow(flow_bus)
                    if flow_value is not None:
                        error = TARGET_FLOW_RATE - flow_value
                        
                        if abs(error) > deadband:
                            adjustment = Kp * error
                            voltage_container['current_voltage'] = max(MIN_VOLTAGE, min(MAX_VOLTAGE, voltage_container['current_voltage'] + adjustment))
                            logger.debug(f"Adjusting voltage to: {voltage_container['current_voltage']}")
                            adjustment_event.set()
                        
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        writer.writerow({'timestamp': current_time, 'flow_value': flow_value, 'voltage': voltage_container['current_voltage']})
                        logger.info(f"Flow Value: {flow_value}, Voltage: {voltage_container['current_voltage']}")
                    time.sleep(SAMPLE_INTERVAL)
            except KeyboardInterrupt:
                logger.info("\nMeasurement stopped by user.")
            finally:
                stop_flow_measurement(flow_bus)
        else:
            logger.error("Failed to start flow measurement.")

def pump_control_thread(sensor_thread, adjustment_event, voltage_container):
    with SMBus(7) as pump_bus:
        run_sequence(pump_bus, voltage_container['current_voltage'])

        while sensor_thread.is_alive():
            if adjustment_event.is_set():
                logger.debug(f"Applying updated voltage: {voltage_container['current_voltage']}")
                run_sequence(pump_bus, voltage_container['current_voltage'])
                adjustment_event.clear()

        stop_pump(pump_bus)

def main():
    adjustment_event = threading.Event()
    sensor_thread = threading.Thread(target=flow_sensor_thread, args=(adjustment_event, voltage_container))
    pump_thread = threading.Thread(target=pump_control_thread, args=(sensor_thread, adjustment_event, voltage_container))

    sensor_thread.start()
    pump_thread.start()

    sensor_thread.join()
    pump_thread.join()

if __name__ == "__main__":
    main()
