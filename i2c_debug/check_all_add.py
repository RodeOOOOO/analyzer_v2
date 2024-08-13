import smbus2

def scan_i2c_bus(bus_number):
    bus = smbus2.SMBus(bus_number)
    devices = []

    for address in range(128):
        try:
            bus.write_byte(address, 0)  # Sending a simple write to check if the device acknowledges
            devices.append(hex(address))
        except OSError as e:
            if e.errno == 121:  # Remote I/O error
                continue  # No device responded at this address
        except Exception as e:
            print(f"Error at address {hex(address)}: {e}")
    
    bus.close()
    return devices

# Scan I2C bus 1
i2c_bus_number = 8
devices_found = scan_i2c_bus(i2c_bus_number)

if devices_found:
    print(f"Devices found on I2C bus {i2c_bus_number}: {', '.join(devices_found)}")
else:
    print(f"No devices found on I2C bus {i2c_bus_number}.")
