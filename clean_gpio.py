import Jetson.GPIO as GPIO
import logging  # Import the logging module
from logger import setup_logger

def clean_up_gpios():
    logger = setup_logger(__name__, level=logging.INFO)

    try:
        logger.info("Cleaning up GPIOs...")
        GPIO.cleanup()
        logger.info("GPIO cleanup completed.")
    except Exception as e:
        logger.error(f"An error occurred during GPIO cleanup: {e}")

if __name__ == "__main__":
    clean_up_gpios()
