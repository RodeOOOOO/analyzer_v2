import smbus2
import time
from prettytable import PrettyTable
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

I2C_LOWDRIVER_ADDRESS = 0x59  # I2C address for mp-Lowdriver

# Initialize I2C bus
bus = smbus2.SMBus(1)  # I2C bus number (usually 1 on Jetson Nano)

# Default values based on the provided table
default_values = {
    0x00: 0x02,
    0x01: 0x38,
    0x02: 0x40,
    0x03: 0x00,
    0x04: 0x00,
    0x05: 0x00,
    0x06: 0x00,
    0x07: 0x00,
    0x08: 0x00,
    0x09: 0x00,
    0x0A: 0x00,
    0x0B: 0x00,
    0xFF: 0x00
}

def read_register(address, reg, length):
    try:
        data = bus.read_i2c_block_data(address, reg, length)
        return data
    except OSError as e:
        print(f"Failed to read from register {hex(reg)} at address {hex(address)}: {e}")
        return None

def select_memory_registers():
    bus.write_byte_data(I2C_LOWDRIVER_ADDRESS, 0xFF, 0x01)
    time.sleep(0.1)
    logging.debug("Selected Memory Registers")

def select_control_registers():
    bus.write_byte_data(I2C_LOWDRIVER_ADDRESS, 0xFF, 0x00)
    time.sleep(0.1)
    logging.debug("Selected Control Registers")

def print_register_table(address, registers, length, default_values, page):
    table = PrettyTable()
    table.field_names = ["Reg #", "Default (Hex)", "Default (Dec)", "Current (Hex)", "Current (Dec)", "7", "6", "5", "4", "3", "2", "1", "0"]

    if page == 'memory':
        select_memory_registers()
    else:
        select_control_registers()

    for reg in registers:
        data = read_register(address, reg, length)
        if data is not None:
            current_value = data[0]
            default_value = default_values.get(reg, 0x00)  # Default to 0x00 if not in default_values
            bits = [int(bit) for bit in format(current_value, '08b')]
            table.add_row([hex(reg), hex(default_value), default_value, hex(current_value), current_value] + bits)
        else:
            table.add_row([hex(reg), 'Error', 'Error', 'Error', 'Error'] + ['Error'] * 8)
    
    print(f"{page.capitalize()} Page")
    print(table)

if __name__ == "__main__":
    # Define the list of registers to read based on the provided table
    control_registers = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B]
    memory_registers = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B]

    # Length of data to read from each register (1 byte for each register as shown in the table)
    read_length = 1

    # Print the control page register table
    print_register_table(I2C_LOWDRIVER_ADDRESS, control_registers, read_length, default_values, page='control')
    
    # Print the memory page register table
    print_register_table(I2C_LOWDRIVER_ADDRESS, memory_registers, read_length, default_values, page='memory')
    
    bus.close()
