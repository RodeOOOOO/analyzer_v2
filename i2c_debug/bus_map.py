import os
import subprocess

def get_i2c_bus_mapping():
    bus_mapping = {}
    i2c_adapters = {
        'i2c@3160000': '/dev/i2c-0',
        'i2c@3180000': '/dev/i2c-1',
        'i2c@3190000': '/dev/i2c-2',
        'i2c@31b0000': '/dev/i2c-3',
        'i2c@31c0000': '/dev/i2c-4',
        'i2c@31e0000': '/dev/i2c-5',
        'i2c@c240000': '/dev/i2c-6',
        'i2c@c250000': '/dev/i2c-7'
    }
    
    for dev_tree_entry, i2c_dev in i2c_adapters.items():
        freq_file_path = f'/proc/device-tree/{dev_tree_entry}/clock-frequency'
        if os.path.exists(freq_file_path):
            try:
                # Use subprocess to call `xxd` and capture the output
                result = subprocess.run(['xxd', '-ps', freq_file_path], stdout=subprocess.PIPE)
                hex_output = result.stdout.decode().strip()
                # Convert the hexadecimal output to decimal
                op_freq_hz = int(hex_output, 16)
                op_freq_khz = op_freq_hz / 1000.0
                bus_mapping[i2c_dev] = {
                    'device_tree_entry': dev_tree_entry,
                    'operating_frequency_hz': op_freq_hz,
                    'operating_frequency_khz': op_freq_khz
                }
            except Exception as e:
                print(f"Failed to read frequency for {i2c_dev}: {e}")
        else:
            print(f"File does not exist: {freq_file_path}")

    return bus_mapping

def main():
    bus_mapping = get_i2c_bus_mapping()
    if bus_mapping:
        print("I2C Bus Mapping (System Bus -> Device Tree Entry, Operating Frequency):")
        for sys_bus, details in bus_mapping.items():
            print(f"{sys_bus} -> Device Tree Entry: {details['device_tree_entry']}, "
                  f"Operating Frequency: {details['operating_frequency_hz']} Hz "
                  f"({details['operating_frequency_khz']} kHz)")
    else:
        print("No I2C buses found or unable to resolve device paths.")

if __name__ == "__main__":
    main()
