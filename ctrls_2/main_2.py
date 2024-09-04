import threading
import logging
import Jetson.GPIO as GPIO
from smbus2 import SMBus
from config import PUMP_CONFIG, FLOW_CONFIG, PROCESS_CONFIG
from flow_control import flow_control_thread
from process import flush_process, homogenization_process, sample_process

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Shared data structure
shared_data = {
    "flow": None,
    "voltage": PUMP_CONFIG['initial_voltage'],
    "target_flow": PROCESS_CONFIG['flush_rate'],
    "elapsed_time": 0,
    "valve_mode": "flush_flow"  # Initial valve mode
}

flow_lock = threading.Lock()
flush_finish_flag = threading.Event()
homogenization_finish_flag = threading.Event()
sample_finish_flag = threading.Event()

def main():
    # Open I2C bus
    with SMBus(PUMP_CONFIG['pump_bus']) as pump_bus, SMBus(FLOW_CONFIG['flow_bus']) as flow_bus:
        
        # Start the thread for monitoring flow and controlling valve mode
        flow_thread = threading.Thread(target=flow_control_thread, args=(pump_bus, flow_bus, shared_data, flow_lock))
        flow_thread.start()

        # Handle the sequence of processes in the main thread
        logger.info("Starting flush process...")
        flush_process(shared_data, flow_lock, flush_finish_flag)

        logger.info("Starting homogenization process...")
        homogenization_process(shared_data, flow_lock, homogenization_finish_flag)

        logger.info("Starting sample process...")
        sample_process(shared_data, flow_lock, sample_finish_flag)

        logger.info("Starting final flush process...")
        flush_process(shared_data, flow_lock, flush_finish_flag)

        # Ensure the flow thread is joined before exiting
        flow_thread.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
