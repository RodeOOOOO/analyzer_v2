import socket
import os
import csv
import time
import numpy as np
import pandas as pd
from config import VNA_CONFIG
from logger import setup_logger
import logging
from datetime import datetime
from processing_manager import ProcessingManager

logger = setup_logger(__name__, level=logging.INFO)

class SocketStreamReader:
    def __init__(self, sock):
        self._sock = sock
        self._recv_buffer = bytearray()

    def readline(self, timeout=5):
        self._sock.settimeout(timeout)
        try:
            return self.readuntil(b"\n")
        except socket.timeout:
            raise TimeoutError("Socket read timed out while waiting for data.")
        finally:
            self._sock.settimeout(None)

    def readuntil(self, separator=b"\n"):
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

    def _recv_into(self, view):
        bytes_read = min(len(view), len(self._recv_buffer))
        view[:bytes_read] = self._recv_buffer[:bytes_read]
        self._recv_buffer = self._recv_buffer[bytes_read:]
        if bytes_read == len(view):
            return bytes_read
        bytes_read += self._sock.recv_into(view[bytes_read:])
        return bytes_read


class libreVNA:
    def __init__(self, host='localhost', port=19542, fetch_timeout=20):
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
        timeout = timeout or self.fetch_timeout
        logger.debug(f"Sending query: {query}")
        self.sock.sendall(query.encode())
        self.sock.send(b"\n")
        response = self.reader.readline(timeout=timeout).decode().rstrip()
        if not response:
            raise ValueError(f"Received empty response for query: {query}")
        logger.debug(f"Received response: {response}")
        return response

    def fetch_s_parameters(self, collect_s21=True, collect_s11=True, collect_s12=True, collect_s22=True):
        logger.info("Fetching selected S-parameter data...")
        try:
            result = {}
            frequency = None

            def parse_trace_data(data, is_first_trace=True):
                data = data.strip("[]").split("],[")
                logger.debug(f"Raw data received: {data[:5]}...")
                if not data:
                    raise ValueError("Trace data is empty or invalid.")
                parsed_points = [list(map(float, point.split(","))) for point in data]
                if is_first_trace:
                    freq, real, imag = zip(*parsed_points)
                    return np.array(freq), np.array(real), np.array(imag)
                else:
                    _, real, imag = zip(*parsed_points)
                    return np.array(real), np.array(imag)

            if collect_s21:
                logger.info("Collecting S21 data...")
                s21_data = self.send_query("VNA:TRACe:DATA? S21")
                if frequency is None:
                    frequency, s21_real, s21_imag = parse_trace_data(s21_data, is_first_trace=True)
                    result["frequency"] = frequency
                else:
                    s21_real, s21_imag = parse_trace_data(s21_data)
                result.update({"s21_real": s21_real, "s21_imag": s21_imag})

            if collect_s11:
                logger.info("Collecting S11 data...")
                s11_data = self.send_query("VNA:TRACe:DATA? S11")
                s11_real, s11_imag = parse_trace_data(s11_data, is_first_trace=False)
                result.update({"s11_real": s11_real, "s11_imag": s11_imag})

            if collect_s12:
                logger.info("Collecting S12 data...")
                s12_data = self.send_query("VNA:TRACe:DATA? S12")
                s12_real, s12_imag = parse_trace_data(s12_data, is_first_trace=False)
                result.update({"s12_real": s12_real, "s12_imag": s12_imag})

            if collect_s22:
                logger.info("Collecting S22 data...")
                s22_data = self.send_query("VNA:TRACe:DATA? S22")
                s22_real, s22_imag = parse_trace_data(s22_data, is_first_trace=False)
                result.update({"s22_real": s22_real, "s22_imag": s22_imag})

            return result

        except Exception as e:
            logger.error(f"An error occurred while fetching S-parameters: {e}")
            logger.debug("Full traceback:", exc_info=True)
            raise

    def close(self):
        if self.sock:
            self.sock.close()
            logger.info("VNA connection closed.")


def wait_for_sweep_completion(vna, poll_interval=1):
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
    logger.info(f"Waiting {delay} seconds post-sweep to fetch data...")
    time.sleep(delay)
    return vna.fetch_s_parameters()


def run_vna_sweep(chemical, concentration, experiment_number):
    try:
        logger.info("Attempting to connect to LibreVNA...")
        vna = libreVNA(host='localhost', port=19542, fetch_timeout=30)
        logger.info("Connected to LibreVNA.")

        # Configure VNA
        vna.send_command(f"VNA:ACQuisition:IFBW {VNA_CONFIG['ifbw']}")
        vna.send_command(f"VNA:ACQuisition:POINTS {VNA_CONFIG['points']}")
        vna.send_command(f"VNA:FREQuency:START {VNA_CONFIG['start_frequency']}")
        vna.send_command(f"VNA:FREQuency:STOP {VNA_CONFIG['stop_frequency']}")

        # Start Sweep
        logger.info("Starting sweep...")
        vna.send_command("VNA:ACQuisition:RUN")
        wait_for_sweep_completion(vna)

        # Fetch S-parameters
        s_parameters = fetch_s_parameters_with_delay(vna, delay=2)

        # Save raw data to the Raw_datalog folder
        if not os.path.exists('Raw_datalog'):
            os.makedirs('Raw_datalog')

        raw_data_filename = (
            f"Raw_datalog/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_chem_{chemical}_conc_{concentration}_exp_{experiment_number}.csv"
        )
        logger.info(f"Saving raw data to {raw_data_filename}...")

        with open(raw_data_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Include chemical, concentration, and experiment number in headers
            writer.writerow([
                "Chemical", "Concentration", "Experiment Number", "Frequency (Hz)",
                "S11 Real", "S11 Imaginary", "S21 Real", "S21 Imaginary",
                "S12 Real", "S12 Imaginary", "S22 Real", "S22 Imaginary"
            ])
            for i in range(len(s_parameters["frequency"])):
                row = [
                    chemical, concentration, experiment_number, s_parameters["frequency"][i],
                    s_parameters.get("s11_real", [None])[i],
                    s_parameters.get("s11_imag", [None])[i],
                    s_parameters.get("s21_real", [None])[i],
                    s_parameters.get("s21_imag", [None])[i],
                    s_parameters.get("s12_real", [None])[i],
                    s_parameters.get("s12_imag", [None])[i],
                    s_parameters.get("s22_real", [None])[i],
                    s_parameters.get("s22_imag", [None])[i],
                ]
                writer.writerow(row)

        logger.info("Raw data saved successfully.")

        # Load raw data into a DataFrame
        raw_data = pd.read_csv(raw_data_filename)

        # Initialize the ProcessingManager
        manager = ProcessingManager(
            baseline_file="baseline.csv",
            processed_dir="processed_data",
            h5_file="data/data.h5"
        )

        # Preprocess and save the data
        manager.process_and_save(raw_data)

        logger.info("Data preprocessing completed and saved successfully.")
        return s_parameters

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e

    finally:
        if 'vna' in locals():
            vna.close()
            logger.info("VNA connection closed.")