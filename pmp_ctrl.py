import smbus2
import time

# Initialize the I2C bus
bus = smbus2.SMBus(7)  # 1 is the I2C bus number, replace if necessary
address = 0x59  # I2C address of the device

# Define the register for changing pages
register_page_ff = 0xFF

# Define waveform data for page 1
waveform_data = [
    0x05,  # Header size (5-1 = 4 bytes for header)
    0x80, 0x06,  # Start address (upper byte 0x80, lower byte 0x06)
    0x00, 0x09,  # Stop address (upper byte 0x00, lower byte 0x09)
    0x00,  # Repeat count (0 = infinite loop)
    0xFF,  # Amplitude (100V, 0xFF for full scale 150V)
    0x0C,  # Frequency (100Hz)
    0x64,  # Cycles (100 cycles)
    0x00  # Envelope (no envelope)
]

# Define control data for page 0
control_data = [0x00, 0x3B, 0x01, 0x01]

def write_waveform_data():
    # Switch to page 1
    bus.write_i2c_block_data(address, register_page_ff, [1])
    print("Switched to page 1")

    # Write waveform data to consecutive registers starting at 0x00
    for i, data in enumerate(waveform_data):
        bus.write_i2c_block_data(address, i, [data])
        print(f"Written to register 0x{i:02X} on page 1: {data}")

    # Small delay to ensure the write operation is completed
    time.sleep(0.2)

def write_control_data():
    # Switch to page 0
    bus.write_i2c_block_data(address, register_page_ff, [0])
    print("Switched to page 0")

    # Write control data to consecutive registers starting at 0x00
    for i, data in enumerate(control_data):
        bus.write_i2c_block_data(address, i, [data])
        print(f"Written to register 0x{i:02X} on page 0: {data}")

    # Small delay to ensure the write operation is completed
    time.sleep(0.2)

# Write waveform data on page 1
write_waveform_data()

# Write control data on page 0
write_control_data()

# Switch back to page 0 before exiting
bus.write_i2c_block_data(address, register_page_ff, [0])
print("Switched back to page 0")

# Close the bus
bus.close()
