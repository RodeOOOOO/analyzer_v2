import time
import threading
from config import PROCESS_CONFIG # Import the process-specific configuration
from valve import control_valve_mode  # Import the valve control function
from vna import run_vna_sweep  # Import the VNA sweep function
from logger import setup_logger
import logging

logger = setup_logger(__name__, level=logging.INFO)

flush_finish_flag = threading.Event()
homogenization_finish_flag = threading.Event()
sample_finish_flag = threading.Event()

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

def sample_process(shared_data, flow_lock, finish_flag, concentration, chemical, experiment_number):
    """Perform the sampling process with VNA sweep."""
    with flow_lock:
        shared_data["target_flow"] = PROCESS_CONFIG['sample_rate']
        shared_data["valve_mode"] = "sample_flow"
    
    logger.debug("Starting sampling process...")
    control_valve_mode(shared_data["valve_mode"])  # Control the valve mode
    
    # Perform the VNA sweep during the sampling process
    logger.info("Starting VNA sweep...")
    run_vna_sweep(chemical, concentration, experiment_number)  # Perform the VNA sweep
    
    # Once VNA sweep is completed, set the finish flag
    finish_flag.set()
    logger.debug("Sampling process completed and VNA sweep finished.")
