import time
from smbus2 import SMBus, i2c_msg

# Initialize the I2C bus
bus = SMBus(1)  # Use 0 for older Raspberry Pi models

# I2C device address
I2C_LOWDRIVER_ADDRESS = 0x59

# Page switch register and data (single-byte write)
PAGE_SWITCH_REGISTER = 0xFF
PAGE0 = 0x00
PAGE1 = 0x01
PAGE2 = 0x02

# Target register and data to write
TARGET_REGISTER_ADDRESS = 0x02
DATA_TO_WRITE = 0x41

# Toggle variable to track the current page
current_page = PAGE0

def switch_page():
    global current_page
    # Determine the new page value
    if current_page == PAGE0:
        new_page = PAGE0
    elif current_page == PAGE1:
        new_page = PAGE1
    else:
        new_page = PAGE2

    # Switch to the new page with a single-byte write to 0xFF
    page_switch_msg = i2c_msg.write(I2C_LOWDRIVER_ADDRESS, [PAGE_SWITCH_REGISTER, new_page])
    bus.i2c_rdwr(page_switch_msg)
    print(f"Switched to page {new_page} by writing to register {PAGE_SWITCH_REGISTER}")

    # Update the current page
    current_page = new_page

# Example usage:
# Switch page
switch_page()
time.sleep(0.1)

# Write to the target register on the new page
bus.write_byte_data(I2C_LOWDRIVER_ADDRESS, TARGET_REGISTER_ADDRESS, DATA_TO_WRITE)
print(f"Written {DATA_TO_WRITE} to register {TARGET_REGISTER_ADDRESS} of device {I2C_LOWDRIVER_ADDRESS}")

# Short delay to ensure the write operation is completed
time.sleep(0.1)

# Read back the data from the target register
read_data = bus.read_byte_data(I2C_LOWDRIVER_ADDRESS, TARGET_REGISTER_ADDRESS)
print(f"Read {read_data} from register {TARGET_REGISTER_ADDRESS} of device {I2C_LOWDRIVER_ADDRESS}")

# Close the bus
bus.close()
