import logging
import os
from datetime import datetime

# Create output_logs and data_logs folders if they don't exist
if not os.path.exists("output_logs"):
    os.makedirs("output_logs")

if not os.path.exists("data_logs"):
    os.makedirs("data_logs")

# Generate a filename for the terminal log
output_log_filename = os.path.join("output_logs", datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))

# Configure the root logger for terminal logs
logging.basicConfig(
    level=logging.DEBUG,  # Root logger level (this won't affect individual loggers)
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(output_log_filename),  # Log to file in output_logs
        logging.StreamHandler()                   # Log to terminal
    ]
)

def setup_logger(name, level=logging.INFO):
    """
    Create or retrieve a logger instance for a specific module or file.

    Args:
        name (str): Name of the logger (usually `__name__`).
        level (int): Logging level for the logger (e.g., logging.DEBUG, logging.INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.hasHandlers():  # Only configure if no handlers exist
        print(f"Logger created: {name}")  # Debug: Track logger creation

        # Stream handler for terminal output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

        # File handler for writing logs
        file_handler = logging.FileHandler(output_log_filename)
        file_handler.setLevel(logging.DEBUG)  # Log all levels to file
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

        # Add handlers to the logger
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    # Set the logging level for this logger
    logger.setLevel(level)

    return logger
