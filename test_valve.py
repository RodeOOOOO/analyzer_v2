import time
from valve import control_valve_mode  # Assuming control_valve_mode is in valve.py
import logging
from logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

def test_control_valve_mode():
    """Test the control_valve_mode function with different modes."""
    
    logger.info("Testing sample_flow mode...")
    control_valve_mode("sample_flow")
    time.sleep(15)
    print("\n")
    
    logger.info("Testing flush_flow mode...")
    control_valve_mode("flush_flow")
    time.sleep(15)
    print("\n")
    
    logger.info("Testing homogenization_flow mode...")
    control_valve_mode("homogenization_flow")
    time.sleep(15)
    print("\n")
    
    logger.info("Testing an unknown valve mode...")
    control_valve_mode("invalid_mode")
    time.sleep(15)
    print("\n")

def main():
    """Main entry point for valve control testing."""
    test_control_valve_mode()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        logger.debug("Test completed.")
