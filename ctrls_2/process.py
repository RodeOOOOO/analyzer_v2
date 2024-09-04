import time
import threading
import logging
from config import PROCESS_CONFIG  # Import the process-specific configuration
from valve import control_valve_mode  # Import the valve control function

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def flush_process(shared_data, flow_lock, finish_flag):
    """Perform the flush process."""
    with flow_lock:
        shared_data["target_flow"] = PROCESS_CONFIG['flush_rate']
        shared_data["valve_mode"] = "flush_flow"
    
    logger.debug("Starting flush process...")
    control_valve_mode(shared_data["valve_mode"])  # Control the valve mode
    time.sleep(PROCESS_CONFIG['flush_time'])  # Simulate the process duration

    finish_flag.set()
    logger.debug("Flush process completed.")

def homogenization_process(shared_data, flow_lock, finish_flag):
    """Perform the homogenization process."""
    with flow_lock:
        shared_data["target_flow"] = PROCESS_CONFIG['homogenization_rate']
        shared_data["valve_mode"] = "homogenization_flow"
    
    logger.debug("Starting homogenization process...")
    control_valve_mode(shared_data["valve_mode"])  # Control the valve mode
    time.sleep(PROCESS_CONFIG['homogenization_time'])

    finish_flag.set()
    logger.debug("Homogenization process completed.")

def sample_process(shared_data, flow_lock, finish_flag):
    """Perform the sampling process."""
    with flow_lock:
        shared_data["target_flow"] = PROCESS_CONFIG['sample_rate']
        shared_data["valve_mode"] = "sample_flow"
    
    logger.debug("Starting sampling process...")
    control_valve_mode(shared_data["valve_mode"])  # Control the valve mode
    
    if PROCESS_CONFIG['sample_time']:
        time.sleep(PROCESS_CONFIG['sample_time'])
    else:
        time.sleep(60)  # Default sample time

    finish_flag.set()
    logger.debug("Sampling process completed.")
