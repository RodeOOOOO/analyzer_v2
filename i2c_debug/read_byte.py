from smbus2 import SMBus
import time
import logging

# Define the I2C address for the low driver
I2C_LOWDRIVER_ADDRESS = 0x59  # Updated I2C device address

class I2CDevice:
    def __init__(self, bus_number):
        self.bus = SMBus(bus_number)
    
    def select_memory_registers(self):
        self.bus.write_byte_data(I2C_LOWDRIVER_ADDRESS, 0xFF, 0x01)
        time.sleep(0.1)
        logging.debug("Selected Memory Registers")
    
    def select_control_registers(self):
        self.bus.write_byte_data(I2C_LOWDRIVER_ADDRESS, 0xFF, 0x00)
        time.sleep(0.1)
        logging.debug("Selected Control Registers")
    
    def read_12_bytes(self, start_register):
        data = []
        
        try:
            # Read 12 bytes from consecutive registers starting from start_register
            for i in range(12):
                register = start_register + i
                byte = self.bus.read_byte_data(I2C_LOWDRIVER_ADDRESS, register)
                data.append(byte)
        except IOError as e:
            print(f"Failed to read data: {e}")
        
        return data
    
    def read_from_both_pages(self, start_register):
        # Select and read from memory registers
        self.select_memory_registers()
        memory_data = self.read_12_bytes(start_register)
        
        # Select and read from control registers
        self.select_control_registers()
        control_data = self.read_12_bytes(start_register)
        
        return memory_data, control_data

# Example usage
bus_number = 1  # Change this to your specific bus number
start_register = 0x00  # Change this to your starting register address

# Create an instance of I2CDevice
device = I2CDevice(bus_number)

# Read the bytes from both pages
memory_data, control_data = device.read_from_both_pages(start_register)

# Print the read bytes in both decimal and hex
print("Memory Registers Data:")
for i, byte in enumerate(memory_data):
    print(f"Register {start_register + i:#04x}: Decimal {byte}, Hex {byte:#04x}")

print("\nControl Registers Data:")
for i, byte in enumerate(control_data):
    print(f"Register {start_register + i:#04x}: Decimal {byte}, Hex {byte:#04x}")

# Close the bus when done
device.bus.close()
