import threading
from smbus2 import SMBus, i2c_msg
import time
import logging
import os
import csv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)  # Change to DEBUG for debugging, INFO to reduce verbosity
logger = logging.getLogger(__name__)

# Constants for the flow sensor
I2C_SLF3S_ADDRESS = 0x08  # Default address for Sensirion SLF3S Flow Sensor (SLF-0600)
SCALE_FACTOR_FLOW = 10000.0  # Since you are using the SLF-0600 model
calibration_cmdByte = 0x08  # Default cmdByte for water measurement

# Constants for the pump driver
PUMP_I2C_ADDRESS = 0x59  # I2C address of the pump driver
REGISTER_PAGE_FF = 0xFF  # Register for changing pages

# Desired voltage
DESIRED_VOLTAGE = 50  # Voltage in volts

# Calculate amplitude value for 40V
AMPLITUDE_VALUE = int((DESIRED_VOLTAGE / 150.0) * 255)

# Data for configuring the pump
WAVEFORM_DATA = [
    0x05,  # Header size (5-1 = 4 bytes for header)
    0x80, 0x06,  # Start address (upper byte 0x80, lower byte 0x06)
    0x00, 0x09,  # Stop address (upper byte 0x00, lower byte 0x09)
    0x00,  # Repeat count (0 = infinite loop)
    AMPLITUDE_VALUE,  # Amplitude for 40V
    0x0C,  # Frequency (100Hz)
    0x64,  # Cycles (100 cycles)
    0x00  # Envelope (no envelope)
]

CONTROL_DATA = [0x00, 0x3B, 0x01, 0x01]  # Control data for page 0

# Duration to run the process (in seconds)
RUN_DURATION = 900

# Sampling interval (in seconds)
SAMPLE_INTERVAL = 0.5  # 0.5 ms delay between readings, you can change this to your desired interval

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

def write_waveform_data(bus, address, register_page_ff, waveform_data):
    # Switch to page 1
    bus.write_i2c_block_data(address, register_page_ff, [1])
    logger.debug("Switched to page 1")

    # Write waveform data to consecutive registers starting at 0x00
    for i, data in enumerate(waveform_data):
        bus.write_i2c_block_data(address, i, [data])
        logger.debug(f"Written to register 0x{i:02X} on page 1: {data}")

    # Small delay to ensure the write operation is completed
    time.sleep(0.2)

def write_control_data(bus, address, register_page_ff, control_data):
    # Switch to page 0
    bus.write_i2c_block_data(address, register_page_ff, [0])
    logger.debug("Switched to page 0")

    # Write control data to consecutive registers starting at 0x00
    for i, data in enumerate(control_data):
        bus.write_i2c_block_data(address, i, [data])
        logger.debug(f"Written to register 0x{i:02X} on page 0: {data}")

    # Small delay to ensure the write operation is completed
    time.sleep(0.2)

def run_sequence(bus):
    # Run the sequence on the pump driver
    write_waveform_data(bus, PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, WAVEFORM_DATA)
    write_control_data(bus, PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, CONTROL_DATA)
    bus.write_i2c_block_data(PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, [0])
    logger.debug("Switched back to page 0 after sequence")

def stop_pump(bus):
    # Set pump voltage to 0 by writing a zero amplitude waveform
    zero_waveform_data = WAVEFORM_DATA[:]
    zero_waveform_data[6] = 0x00  # Set amplitude to 0
    write_waveform_data(bus, PUMP_I2C_ADDRESS, REGISTER_PAGE_FF, zero_waveform_data)
    logger.info("Pump voltage set to 0.")

def flow_sensor_thread():
    # Create 'data' directory if it doesn't exist
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Generate the file name based on the current date, time, and set voltage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{data_dir}/flow_data_{timestamp}_voltage_{DESIRED_VOLTAGE}V.csv"
    
    with SMBus(1) as flow_bus, open(file_name, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'flow_value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        time.sleep(1)  # Allow sensor to stabilize
        if start_flow_measurement(flow_bus):
            try:
                start_time = time.time()
                while time.time() - start_time < RUN_DURATION:
                    flow_value = read_flow(flow_bus)
                    if flow_value is not None:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        writer.writerow({'timestamp': current_time, 'flow_value': flow_value})
                        logger.info(f"Flow Value: {flow_value}")
                    time.sleep(SAMPLE_INTERVAL)  # Use the defined sample interval
            except KeyboardInterrupt:
                logger.info("\nMeasurement stopped by user.")
            finally:
                stop_flow_measurement(flow_bus)
        else:
            logger.error("Failed to start flow measurement.")

def pump_control_thread():
    with SMBus(7) as pump_bus:
        start_time = time.time()
        for _ in range(2):
            run_sequence(pump_bus)
        elapsed_time = time.time() - start_time
        logger.info(f"Total time for both pump sequences: {elapsed_time:.2f} seconds")

        # Run for the specified duration
        time.sleep(RUN_DURATION)

        # Stop the pump after the specified duration
        stop_pump(pump_bus)

def main():
    # Create and start threads for pump control and flow sensor
    pump_thread = threading.Thread(target=pump_control_thread)
    sensor_thread = threading.Thread(target=flow_sensor_thread)

    pump_thread.start()
    sensor_thread.start()

    # Wait for both threads to finish
    pump_thread.join()
    sensor_thread.join()

if __name__ == "__main__":
    main()
