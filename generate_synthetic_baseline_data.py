import pandas as pd
import numpy as np
import os

point_count = 100
# Directory and file path for the synthetic baseline
baseline_dir = "."
baseline_file = os.path.join(baseline_dir, "baseline.csv")

# Create synthetic baseline data
frequency_range = np.linspace(1e6, 6e9, point_count)  # 1 MHz to 6 GHz with 500 points
baseline_permittivity = 2.2 + 0.01 * np.sin(2 * np.pi * frequency_range / 1e9)  # Slight variation
baseline_conductivity = 0.01 + 0.005 * np.cos(2 * np.pi * frequency_range / 1e9)  # Slight variation

# Combine into a DataFrame
baseline_data = pd.DataFrame({
    "Frequency (Hz)": frequency_range,
    "Baseline_Permittivity": baseline_permittivity,
    "Baseline_Conductivity": baseline_conductivity
})

# Save to CSV
baseline_data.to_csv(baseline_file, index=False)

baseline_file
