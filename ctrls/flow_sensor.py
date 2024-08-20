import time
import logging
import os
import csv
from datetime import datetime
from smbus2 import SMBus, i2c_msg
from config import FLOW_SENSOR_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

I2C_SLF3S_ADDRESS = FLOW_SENSOR_CONFIG['i2c_address']
SCALE_FACTOR_FLOW = FLOW_SENSOR_CONFIG['scale_factor_flow']

def start_flow_measurement(bus):
    logger.info("Starting continuous measurement...")
    try:
        bus.write_i2c_block_data(I2C_SLF3S_ADDRESS, 0x36, [FLOW_SENSOR_CONFIG['calibration_cmd_byte']], force=True)
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
    logger.debug(f"Raw sensor data: {data}")

    sensor_flow_value = (data[0] << 8) | data[1]
    signed_flow_value = int.from_bytes(sensor_flow_value.to_bytes(2, byteorder='big'), byteorder='big', signed=True)
    scaled_flow_value = float(signed_flow_value) / SCALE_FACTOR_FLOW
    
    return scaled_flow_value

def monitor_flow_sensor():
    with SMBus(1) as flow_bus:
        time.sleep(1)
        if start_flow_measurement(flow_bus):
            try:
                start_time = time.time()
                homogenization_end_time = start_time + FLOW_SENSOR_CONFIG['homogenization_duration']

                while time.time() - start_time < FLOW_SENSOR_CONFIG['run_duration']:
                    flow_value = read_flow(flow_bus)
                    if flow_value is None:
                        flow_value = 0.0  # Default to 0 if reading fails

                    logger.info(f"Flow Value: {flow_value:.3f} ml/min")

                    time.sleep(FLOW_SENSOR_CONFIG['sample_interval'])
            except KeyboardInterrupt:
                logger.info("Measurement stopped by user.")
            finally:
                stop_flow_measurement(flow_bus)
        else:
            logger.error("Failed to start flow measurement.")
