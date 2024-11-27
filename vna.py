import socket
import os
import csv
import time
import numpy as np
from config import VNA_CONFIG
from logger import setup_logger
import logging

logger = setup_logger(__name__, level=logging.INFO)

class SocketStreamReader:
    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._recv_buffer = bytearray()

    def readline(self, timeout=5) -> bytes:
        """Read a line from the socket stream within the specified timeout."""
        self._sock.settimeout(timeout)
        try:
            return self.readuntil(b"\n")
        except socket.timeout:
            raise TimeoutError("Socket read timed out while waiting for data.")
        finally:
            self._sock.settimeout(None)

    def readuntil(self, separator: bytes = b"\n") -> bytes:
        chunk = bytearray(4096)
        start = 0
        buf = bytearray(len(self._recv_buffer))
        bytes_read = self._recv_into(memoryview(buf))
        while True:
            idx = buf.find(separator, start)
            if idx != -1:
                break
            start = len(self._recv_buffer)
            bytes_read = self._recv_into(memoryview(chunk))
            buf += memoryview(chunk)[:bytes_read]
        result = bytes(buf[: idx + 1])
        self._recv_buffer = b"".join((memoryview(buf)[idx + 1:], self._recv_buffer))
        return result

    def _recv_into(self, view: memoryview) -> int:
        bytes_read = min(len(view), len(self._recv_buffer))
        view[:bytes_read] = self._recv_buffer[:bytes_read]
        self._recv_buffer = self._recv_buffer[bytes_read:]
        if bytes_read == len(view):
            return bytes_read
        bytes_read += self._sock.recv_into(view[bytes_read:])
        return bytes_read


class libreVNA:
    def __init__(self, host='localhost', port=19542, fetch_timeout=20):
        """
        Initialize the VNA connection.

        Args:
            host (str): Host address of the VNA.
            port (int): Port number of the VNA.
            fetch_timeout (int): Timeout in seconds for fetching data.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fetch_timeout = fetch_timeout
        try:
            self.sock.connect((host, port))
        except Exception as e:
            raise Exception("Unable to connect to LibreVNA-GUI. Ensure it is running and the TCP server is enabled.") from e
        self.reader = SocketStreamReader(self.sock)

    def send_command(self, command):
        logger.debug(f"Sending command: {command}")
        self.sock.sendall(command.encode())
        self.sock.send(b"\n")
    
    def send_query(self, query, timeout=None):
        """
        Send a query to the VNA and wait for a response.

        Args:
            query (str): The command to send.
            timeout (int): Timeout in seconds for the query (default: None, uses class fetch_timeout).
        
        Returns:
            str: The response from the VNA.

        Raises:
            ValueError: If the response format is invalid.
        """
        timeout = timeout or self.fetch_timeout
        logger.debug(f"Sending query: {query}")
        self.sock.sendall(query.encode())
        self.sock.send(b"\n")
        response = self.reader.readline(timeout=timeout).decode().rstrip()
        if not response:
            raise ValueError(f"Received empty response for query: {query}")
        logger.debug(f"Received response: {response}")
        return response

    def fetch_s_parameters(self, params_to_fetch=["S11", "S21"]):
        """
        Fetch frequency and specified S-parameters from the VNA.

        Args:
            params_to_fetch (list): List of S-parameters to fetch (e.g., ["S11", "S21"]).

        Returns:
            dict: A dictionary containing frequency and the requested S-parameters.
        """
        logger.info("Fetching frequency and S-parameter data...")

        # Fetch frequency points
        frequency_data = self.send_query("VNA:FREQ?").strip("[]").split(",")
        if not frequency_data:
            raise ValueError("Frequency data is empty or invalid.")
        frequency = np.array([float(freq) for freq in frequency_data], dtype=np.float64)

        # Fetch specified S-parameters
        results = {"frequency": frequency}
        for param in params_to_fetch:
            raw_data = self.send_query(f"VNA:TRACe:DATA? {param}").strip("[]").split("],[")
            if not raw_data:
                raise ValueError(f"{param} data is empty or invalid.")
            results[f"{param.lower()}_real"] = np.array(
                [float(point.split(",")[0]) for point in raw_data], dtype=np.float64
            )
            results[f"{param.lower()}_imag"] = np.array(
                [float(point.split(",")[1]) for point in raw_data], dtype=np.float64
            )
            logger.info(f"Fetched {len(raw_data)} points for {param}.")

        return results

    def close(self):
        """Close the connection to the VNA."""
        if self.sock:
            self.sock.close()
            logger.info("VNA connection closed.")


def wait_for_sweep_completion(vna, poll_interval=1):
    """
    Wait for the VNA sweep to complete by polling *OPC?.
    
    Args:
        vna (libreVNA): Instance of the libreVNA class.
        poll_interval (int): Time (in seconds) to wait between polls.
    """
    logger.info("Waiting for sweep to complete...")
    while True:
        try:
            operation_complete = vna.send_query("*OPC?", timeout=5)
            if operation_complete == "1":
                logger.info("Sweep completed successfully.")
                return
        except TimeoutError as e:
            logger.warning(f"Timeout while polling sweep completion: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while polling sweep completion: {e}")
            raise
        time.sleep(poll_interval)


def fetch_s_parameters_with_delay(vna, delay=2):
    """
    Fetch frequency and S-parameter data after a delay to ensure readiness.

    Args:
        vna (libreVNA): Instance of the libreVNA class.
        delay (int): Delay in seconds before fetching data.

    Returns:
        dict: A dictionary containing frequency and S-parameter data.
    """
    logger.info(f"Waiting {delay} seconds post-sweep to fetch data...")
    time.sleep(delay)
    return vna.fetch_s_parameters()


def run_vna_sweep(concentration, chemical):
    """
    Conduct a VNA sweep, collect S-parameter data, and save it.

    Args:
        concentration (float): The chemical concentration being analyzed (e.g., 500ppm).
        chemical (str): Name of the chemical being analyzed.
    """
    try:
        logger.info("Attempting to connect to LibreVNA...")
        vna = libreVNA(host='localhost', port=19542, fetch_timeout=30)
        logger.info("Connected to LibreVNA.")

        # Configure the VNA
        vna.send_command(f"VNA:ACQuisition:IFBW {VNA_CONFIG['ifbw']}")
        vna.send_command(f"VNA:ACQuisition:POINTS {VNA_CONFIG['points']}")
        vna.send_command(f"VNA:FREQuency:START {VNA_CONFIG['start_frequency']}")
        vna.send_command(f"VNA:FREQuency:STOP {VNA_CONFIG['stop_frequency']}")
        
        # Start the sweep
        logger.info("Starting sweep...")
        vna.send_command("VNA:ACQuisition:RUN")

        # Wait for the sweep to complete
        wait_for_sweep_completion(vna)

        # Fetch frequency and S-parameter data after a delay
        s_parameters = fetch_s_parameters_with_delay(vna, delay=2)

        # Save data to CSV
        if not os.path.exists('data'):
            os.makedirs('data')

        filename = f'data/{concentration}ppm_{chemical}.csv'
        logger.info(f"Saving data to {filename}...")
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Frequency (Hz)", "S11 Real", "S11 Imaginary", "S21 Real", "S21 Imaginary"])

            for i in range(len(s_parameters["frequency"])):
                writer.writerow([
                    s_parameters["frequency"][i],
                    s_parameters["s11_real"][i],
                    s_parameters["s11_imag"][i],
                    s_parameters["s21_real"][i],
                    s_parameters["s21_imag"][i]
                ])
        
        logger.info("Data saved successfully.")
        return s_parameters

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e
    finally:
        if 'vna' in locals():
            vna.close()
