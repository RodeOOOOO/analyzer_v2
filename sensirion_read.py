from smbus2 import SMBus, i2c_msg
import time

I2C_SLF3S_ADDRESS = 0x08  # Default address for Sensirion SLF3S Flow Sensor (SLF-0600)

SCALE_FACTOR_FLOW = 10000.0  # Since you are using the SLF-0600 model
calibration_cmdByte = 0x08  # Default cmdByte for water measurement

def start_flow_measurement(bus):
    print("Starting continuous measurement...")
    try:
        bus.write_i2c_block_data(I2C_SLF3S_ADDRESS, 0x36, [calibration_cmdByte], force=True)
    except OSError as e:
        print(f"Error starting continuous measurement: {e}")
        return False
    return True

def stop_flow_measurement(bus):
    print("Stopping continuous measurement...")
    try:
        bus.write_i2c_block_data(I2C_SLF3S_ADDRESS, 0x3F, [0xF9], force=True)
    except OSError as e:
        print(f"Error stopping continuous measurement: {e}")

def read_flow(bus):
    try:
        msg = i2c_msg.read(I2C_SLF3S_ADDRESS, 3)
        bus.i2c_rdwr(msg)
    except OSError as e:
        print(f"Error reading from sensor: {e}")
        return None
    
    data = list(msg)
    sensor_flow_value = (data[0] << 8) | data[1]
    
    signed_flow_value = int.from_bytes(sensor_flow_value.to_bytes(2, byteorder='big'), byteorder='big', signed=True)
    scaled_flow_value = float(signed_flow_value) / SCALE_FACTOR_FLOW
    
    return scaled_flow_value

# Main Execution
with SMBus(1) as bus:  # Assuming you're using I2C bus 1
    if start_flow_measurement(bus):
        try:
            while True:
                flow_value = read_flow(bus)
                if flow_value is not None:
                    print("Flow Value:", flow_value)
                time.sleep(0.5)  # Delay between readings (adjust as needed)
        except KeyboardInterrupt:
            print("\nMeasurement stopped by user.")
        finally:
            stop_flow_measurement(bus)
    else:
        print("Failed to start flow measurement.")
