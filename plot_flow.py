import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import re
import os

# Path to your CSV file
file_path = 'data/900_s_53V_adp_v_0.4_ml_min_20240812_173457.csv'

# Extract details from the file name using regular expressions
file_name = os.path.basename(file_path)
pattern = r'(\d+)_s_(\d+V)_adp_v_(\d+\.?\d*)_ml_min'
match = re.search(pattern, file_name)

if match:
    duration = int(match.group(1)) / 60  # Convert seconds to minutes
    voltage_value = match.group(2)
    target_flow_rate = match.group(3)
    plot_title = f'Flow over {duration:.1f} mins starting at {voltage_value}, Target {target_flow_rate} ml/min'
else:
    plot_title = "Flow Value Over Time"

# Read the data from the CSV file
df = pd.read_csv(file_path, parse_dates=['timestamp'])

# Convert timestamp to relative time in seconds
df['relative_time'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()

# Reshape the data for linear regression model
X = df['relative_time'].values.reshape(-1, 1)
y = df['flow_value'].values

# Perform linear regression for flow value
flow_model = LinearRegression()
flow_model.fit(X, y)

# Predict flow values using the linear regression model
flow_pred = flow_model.predict(X)

# Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot flow values
ax1.plot(df['relative_time'], df['flow_value'], linestyle='-', label='Flow Value', color='blue')
ax1.plot(df['relative_time'], flow_pred, linestyle='-', color='red', label=f'Flow Linear Regression (y = {flow_model.coef_[0]:.4f}x + {flow_model.intercept_:.4f})')
ax1.set_xlabel('Relative Time (seconds)')
ax1.set_ylabel('Flow Value (ml/min)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.legend(loc='upper left')

# Create a secondary y-axis for voltage
ax2 = ax1.twinx()
ax2.plot(df['relative_time'], df['voltage'], linestyle='-', color='green', label='Voltage')
ax2.set_ylabel('Voltage (V)', color='green')
ax2.tick_params(axis='y', labelcolor='green')
ax2.legend(loc='upper right')

# Set the title
plt.title(plot_title)
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

# Create the visuals directory if it doesn't exist
visuals_dir = os.path.join(os.path.dirname(__file__), 'visuals')
os.makedirs(visuals_dir, exist_ok=True)

# Save the plot
plot_path = os.path.join(visuals_dir, f'{os.path.splitext(file_name)[0]}.png')
plt.savefig(plot_path)

# Show the plot
plt.show()
