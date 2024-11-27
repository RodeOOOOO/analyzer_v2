import Jetson.GPIO as GPIO
import time
import logging
from smbus2 import SMBus
from pump import run_sequence
#from config import PUMP_CONFIG

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GPIO setup
gpio_pin_1 = 15  # Valve 1
gpio_pin_2 = 13  # Valve 2

GPIO.setmode(GPIO.BOARD)
GPIO.setup(gpio_pin_1, GPIO.OUT)
GPIO.setup(gpio_pin_2, GPIO.OUT)

# Variable to hold the valve state
valve_state = {
    "valve_1": None,  # Track state for valve 1 (Pin 1)
    "valve_2": None   # Track state for valve 2 (Pin 2)
}

def update_valve_state(valve_1_state, valve_2_state):
    """Update the valve state and reflect in the debug logs."""
    valve_state['valve_1'] = 'HIGH' if valve_1_state else 'LOW'
    valve_state['valve_2'] = 'HIGH' if valve_2_state else 'LOW'
    
    logger.debug(f"Valve 1 (Pin 1): {valve_state['valve_1']}, Valve 2 (Pin 2): {valve_state['valve_2']}")

def sample_flow():
    """Activate valve configuration for sampling flow."""
    logger.debug("Switching to sample flow...")
    GPIO.output(gpio_pin_1, GPIO.HIGH)
    GPIO.output(gpio_pin_2, GPIO.LOW)
    update_valve_state(GPIO.HIGH, GPIO.LOW)
    logger.debug("Switched to sample flow")

def flush_flow():
    """Activate valve configuration for cleaning flow."""
    logger.debug("Switching to clean flow...")
    GPIO.output(gpio_pin_1, GPIO.LOW)
    GPIO.output(gpio_pin_2, GPIO.HIGH)
    update_valve_state(GPIO.LOW, GPIO.HIGH)
    logger.debug("Switched to flush flow")

def homogenization_flow():
    """Activate valve configuration for homogenization flow."""
    logger.debug("Switching to homogenization flow...")
    GPIO.output(gpio_pin_1, GPIO.LOW)
    GPIO.output(gpio_pin_2, GPIO.LOW)
    update_valve_state(GPIO.LOW, GPIO.LOW)
    logger.debug("Switched to homogenization flow")

def control_valve_mode(valve_mode):
    """Control valves based on the valve mode."""
    logger.debug(f"Controlling valve mode: {valve_mode}")
    try:
        if valve_mode == "sample_flow":
            sample_flow()
        elif valve_mode == "flush_flow":
            flush_flow()
        elif valve_mode == "homogenization_flow":
            homogenization_flow()
        else:
            logger.error(f"Unknown valve mode: {valve_mode}")
    except Exception as e:
        logger.error(f"Error controlling valve mode {valve_mode}: {e}")

def individual_valve_test(valve, interval):
    """Toggles valve state individually for debug."""
    logger.debug(f"Testing valve {valve} with interval {interval}s")
    GPIO.output(valve, GPIO.LOW)
    if valve == gpio_pin_1:
        update_valve_state(GPIO.LOW, valve_state['valve_2'])
    else:
        update_valve_state(valve_state['valve_1'], GPIO.LOW)
    logger.debug(f"Valve {valve}: off")
    time.sleep(interval)
    
    GPIO.output(valve, GPIO.HIGH)
    if valve == gpio_pin_1:
        update_valve_state(GPIO.HIGH, valve_state['valve_2'])
    else:
        update_valve_state(valve_state['valve_1'], GPIO.HIGH)
    logger.debug(f"Valve {valve}: on")
    time.sleep(interval)

def test_pin_32():
    """Test GPIO pin 32 manually."""
    logger.debug("Setting Pin 32 to LOW")
    GPIO.output(gpio_pin_2, GPIO.LOW)
    time.sleep(30)
    logger.debug("Setting Pin 32 to HIGH")
    GPIO.output(gpio_pin_2, GPIO.HIGH)
    time.sleep(2)
    
'''
def test_valve_mode(valve_mode_function):
    """Test valve control along with pump operation."""
    try:
        # Setup I2C bus for pump communication
        with SMBus(PUMP_CONFIG['pump_bus']) as pump_bus:
            # Run the pump with a set voltage, e.g., 50V
            run_sequence(pump_bus, 50)
            logger.info('Pump is running at 50V')

            # Switch valve to the specified mode
            valve_mode_function()
            time.sleep(30)
            print("flow finised")

    except Exception as e:
        logger.error(f"Error during valve mode test: {e}")
'''      

def main():
    """Main entry point for valve control testing."""
    logger.debug("Starting main valve test sequence")
    
    # Uncomment below to test individual valve control
    # individual_valve_test(gpio_pin_1, 2)
    # individual_valve_test(gpio_pin_2, 2)
    
    # Test valve control mode and pump operation
    #test_valve_mode(sample_flow)
    #test_valve_mode(flush_flow)
    test_valve_mode(homogenization_flow)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        GPIO.cleanup()
        logger.debug("GPIO cleanup done.")
        logger.error(f"Error occurred: {e}")
    finally:
        logger.debug("GPIO cleanup done.")
        logger.debug("Process complete.")
