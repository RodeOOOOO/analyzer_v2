import Jetson.GPIO as GPIO

def clean_up_gpios():
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        logger.info("Cleaning up GPIOs...")
        GPIO.cleanup()
        logger.info("GPIO cleanup completed.")
    except Exception as e:
        logger.error(f"An error occurred during GPIO cleanup: {e}")

if __name__ == "__main__":
    clean_up_gpios()
