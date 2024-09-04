PUMP_CONFIG = {
    'i2c_address': 0x59,
    'register_page_ff': 0xFF,
    'control_data': [0x00, 0x3B, 0x01, 0x01],
    'min_voltage': 0,
    'max_voltage': 100,
    'initial_voltage': 0,  # Start with the pump off
    'voltage_step': 0.5,
    'pump_bus': 7
}

FLOW_CONFIG = {
    'i2c_address': 0x08,
    'scale_factor_flow': 10000.0,
    'calibration_cmd_byte': 0x08,
    'run_duration': 1800,  # Total run duration in seconds
    'sample_interval': 0.5,  # Interval between samples in seconds
    'kp': 20.0,  # Proportional control constant directly in the config
    'deadband': 0.1,  # Base deadband value directly in the config
    'flow_bus': 1  # I2C bus number for the flow sensor
}

PROCESS_CONFIG = {
    'flush_rate': 1.0,                # Target flow rate during the flush operation
    'flush_time': 120,                # Time to flush the system before starting the actual process (in seconds)
    'homogenization_rate': 1.0,       # Target flow rate during homogenization (usually same as flush rate)
    'homogenization_time': 120,       # Time allowed for the system to stabilize before data collection (in seconds)
    'sample_rate': 0.4,               # Target flow rate during the sampling process
    'sample_time': None,              # Time for the sampling process (in seconds), if needed
}

VNA_CONFIG = {
    'ifbw': 100,              # IF Bandwidth in Hz
    'points': 10000,          # Number of points
    'start_frequency': 0,     # Start frequency in Hz
    'stop_frequency': 6e9     # Stop frequency in Hz
}

def calculate_deadband(kp, base_kp=FLOW_CONFIG['kp'], base_deadband=FLOW_CONFIG['deadband']):
    """Calculate the deadband based on the proportional control constant (Kp)."""
    return base_deadband * (base_kp / kp)
