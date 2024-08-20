BASE_KP = 10.0  # Base proportional control constant
BASE_DEADBAND = 0.01  # Base deadband value

def calculate_deadband(kp, base_kp=BASE_KP, base_deadband=BASE_DEADBAND):
    return base_deadband * (base_kp / kp)  # Adjust deadband inversely to Kp

PUMP_CONTROL_CONFIG = {
    'i2c_address': 0x59,
    'register_page_ff': 0xFF,
    'control_data': [0x00, 0x3B, 0x01, 0x01],
    'homogenization_voltage': 140,  # Start voltage for homogenization
    'homogenization_duration': 5,  # Duration for homogenization in seconds
    'min_voltage': 0,  # Minimum allowed voltage
    'max_voltage': 150  # Maximum allowed voltage
}

FLOW_SENSOR_CONFIG = {
    'i2c_address': 0x08,
    'scale_factor_flow': 10000.0,
    'calibration_cmd_byte': 0x08,
    'target_flow_rate': 0.4,  # Target flow rate in ml/min
    'run_duration': 1800,  # Total run duration in seconds
    'sample_interval': 0.5,  # Interval between samples in seconds
    'kp': BASE_KP,  # Proportional control constant
    'deadband': calculate_deadband(BASE_KP)  # Calculate deadband based on Kp
}
