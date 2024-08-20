import time
import logging
from smbus2 import SMBus
from config import PUMP_CONTROL_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_waveform_data(bus, voltage):
    amplitude_value = int((voltage / 150.0) * 255)
    
    waveform_data = [
        0x05, 0x80, 0x06, 0x00, 0x09, 0x00, 
        amplitude_value, 0x0C, 0x64, 0x00
    ]
    
    bus.write_i2c_block_data(PUMP_CONTROL_CONFIG['i2c_address'], PUMP_CONTROL_CONFIG['register_page_ff'], [1])
    
    for i, data in enumerate(waveform_data):
        bus.write_i2c_block_data(PUMP_CONTROL_CONFIG['i2c_address'], i, [data])
    
    time.sleep(0.2)

def write_control_data(bus):
    bus.write_i2c_block_data(PUMP_CONTROL_CONFIG['i2c_address'], PUMP_CONTROL_CONFIG['register_page_ff'], [0])
    
    for i, data in enumerate(PUMP_CONTROL_CONFIG['control_data']):
        bus.write_i2c_block_data(PUMP_CONTROL_CONFIG['i2c_address'], i, [data])
    
    time.sleep(0.2)

def run_sequence(bus, voltage):
    for _ in range(2):  # Loop twice
        write_waveform_data(bus, voltage)
        write_control_data(bus)
        bus.write_i2c_block_data(PUMP_CONTROL_CONFIG['i2c_address'], PUMP_CONTROL_CONFIG['register_page_ff'], [0])
        # Optional: Add a small delay if needed between the two iterations
        time.sleep(0.1)

def stop_pump(bus):
    write_waveform_data(bus, 0)
