import socket
import os
import csv
import time
import logging

logger = logging.getLogger(__name__)

class SocketStreamReader:
    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._recv_buffer = bytearray()

    def readline(self) -> bytes:
        return self.readuntil(b"\n")

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
    def __init__(self, host='localhost', port=19542):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
        except Exception as e:
            raise Exception("Unable to connect to LibreVNA-GUI. Ensure it is running and the TCP server is enabled.") from e
        self.reader = SocketStreamReader(self.sock)

    def send_command(self, command):
        logger.debug(f"Sending command: {command}")
        self.sock.sendall(command.encode())
        self.sock.send(b"\n")
    
    def send_query(self, query):
        logger.debug(f"Sending query: {query}")
        self.sock.sendall(query.encode())
        self.sock.send(b"\n")
        response = self.reader.readline().decode().rstrip()
        logger.debug(f"Received response: {response}")
        return response

def run_vna_sweep(concentration, chemical):
    try:
        logger.info("Attempting to connect to LibreVNA...")
        vna = libreVNA(host='localhost', port=19542)
        logger.info("Connected to LibreVNA.")

        # Set IF Bandwidth to 100 Hz
        vna.send_command("VNA:ACQuisition:IFBW 100")
        
        # Set number of points to 10,000
        vna.send_command("VNA:ACQuisition:POINTS 10000")
        
        # Set start frequency to 100 MHz
        vna.send_command("VNA:FREQuency:START 100000000")
        
        # Set stop frequency to 6 GHz
        vna.send_command("VNA:FREQuency:STOP 6000000000")
        
        # Set to single sweep mode
        vna.send_command("VNA:ACQuisition:TYPE SINGLE")
        
        # Start the sweep
        logger.info("Starting sweep...")
        start_time = time.time()
        vna.send_command("VNA:ACQuisition:RUN")
        
        # Wait for the sweep to complete using *OPC?
        logger.info("Waiting for sweep to complete...")
        operation_complete = vna.send_query("*OPC?")
        if operation_complete == "1":
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"Sweep completed successfully in {elapsed_time:.2f} seconds.")
        
        # Extract S12 data after sweep completes
        data = vna.send_query("VNA:TRACe:DATA? S12")

        # Save data to CSV
        if not os.path.exists('data'):
            os.makedirs('data')

        filename = f'data/{concentration}ppm_{chemical}.csv'
        logger.info(f"Saving data to {filename}...")
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Frequency (Hz)", "S12 Real", "S12 Imaginary"])

            # Parse the data correctly
            data_points = data.strip("[]").split("],[")
            for point in data_points:
                freq, s12_real, s12_imag = point.split(",")
                writer.writerow([freq, s12_real, s12_imag])
        
        logger.info("Data saved successfully.")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    
    finally:
        if 'vna' in locals():
            logger.info("Closing the VNA connection...")
            del vna
            logger.info("VNA connection closed.")
