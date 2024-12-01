import os
import csv
from datetime import datetime
import logging

# Ensure directories exist
if not os.path.exists("Raw_datalog"):
    os.makedirs("Raw_datalog")

if not os.path.exists("output_logs"):
    os.makedirs("output_logs")

# Setup logger
def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        file_handler = logging.FileHandler(
            os.path.join("output_logs", datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logger(__name__)
