'''

Data format:

timestamp (float): Time in seconds since the start of the test.
temperature (float): Temperature reading in Celsius.
vibration_x (float): Vibration reading along the X-axis (in arbitrary units).
vibration_y (float): Vibration reading along the Y-axis (in arbitrary units).
voltage (float): Voltage reading (in Volts).

'''

'''

Example data line:
{'timestamp': 0.0, 'temperature': 25.0, 'vibration_x': 1.0, 'vibration_y': 1.0, 'voltage': 5.0}

'''

'''
Anomaly Detection Rules:

Temperature Drift: If the temperature changes by more than ±5 ∘C within a 
                60-second rolling window, it's flagged as a potential drift anomaly.

Excessive Vibration: If the combined magnitude of vibration (vibration_x^2 + vibration_y^2)
                exceeds a threshold of 10.0 at any point, it's flagged as excessive vibration.

Voltage Drop: If the voltage drops below 4.5V for more than 10 consecutive readings, it's 
                flagged as a sustained voltage drop.

'''

# return dictionary

# anomalies: list of dicts describing anomaly
# - type: (str) 'temperature_drift', 'excessive_vibration', or 'voltage_drop'
# - timestamp: (float) timestamp at which anomaly first detected
# - details: (str) [optional] additonal info about anomaly

# summary: dict containing total count of each type detected
# - temperature_drift_count (int)
# - excessive_vibration_count (int)
# - voltage_drop_count (int)

import math
import json
from collections import deque


def check_excessive_vibration(data_line, anomalies, excessive_vibration_count):
    # check vibration against threshold
    magnitude = math.sqrt(data_line['vibration_x']**2 + data_line['vibration_y']**2)
    if magnitude > 10.0:
        # found excessive vibration, increment count and add info to list
        excessive_vibration_count += 1
        anomalies.append({'type': 'excessive_vibration', 
                              'timestamp': data_line['timestamp'], 
                              'details': f'Combined Magnitude: {magnitude}'})
    return anomalies, excessive_vibration_count


def check_temperature_drift(data_line, anomalies, temperature_drift_count, time_window):
    temperatures_in_window = [item['temperature'] for item in time_window]
    if temperatures_in_window:
        max_temp = max(temperatures_in_window)
        min_temp = min(temperatures_in_window)
        if abs(max_temp - min_temp) > 5:
            temperature_drift_count += 1
            anomalies.append({'type': 'temperature_drift', 
                              'timestamp': data_line['timestamp'], 
                              'details': f'Temperature Change: {abs(max_temp - min_temp)} Degrees C'})
    return anomalies, temperature_drift_count

def check_voltage_drop(data_line, anomalies, voltage_drop_count, previous_voltage, consecutive_lows):
    # first data point, so save voltage and move on
    if previous_voltage == 0:
        previous_voltage = data_line['voltage']

    # check for low voltage, incrementing count
    elif previous_voltage < 4.5 and data_line['voltage'] < 4.5 and consecutive_lows < 9:
        consecutive_lows += 1
        previous_voltage = data_line['voltage']

    # check for hitting consecutive count, add anomaly
    elif previous_voltage < 4.5 and data_line['voltage'] < 4.5 and consecutive_lows > 9:
        # triggers anomaly
        previous_voltage = data_line['voltage']
        voltage_drop_count += 1
        anomalies.append({'type': 'voltage_drop', 
                          'timestamp': data_line['timestamp']})
    
    # reset consecutive lows if we find one over the threshold
    if data_line['voltage'] >= 4.5:
        consecutive_lows = 0

    return anomalies, voltage_drop_count, previous_voltage, consecutive_lows

def analyze_test_data(test_data):
    anomalies = []
    summary = {'temperature_drift_count': 0, 
               'excessive_vibration_count': 0,
               'voltage_drop_count': 0}

    temperature_drift_count = 0
    excessive_vibration_count = 0
    voltage_drop_count = 0

    time_window = deque()

    previous_voltage = 0
    consecutive_lows = 0

    # iterate test data
    for data_line in test_data:

        # Start keeping track of 60s sliding window
        current_time = data_line['timestamp']
        time_window.append(data_line)
        while time_window and time_window[0]['timestamp'] < current_time - 60:
            time_window.popleft()
        
        # check the window for temperature drift
        if time_window:
            anomalies, temperature_drift_count = check_temperature_drift(data_line, anomalies, temperature_drift_count, time_window)

        anomalies, voltage_drop_count, previous_voltage, consecutive_lows = check_voltage_drop(data_line, anomalies, voltage_drop_count, previous_voltage, consecutive_lows)

        anomalies, excessive_vibration_count = check_excessive_vibration(data_line, anomalies, excessive_vibration_count)

    summary = {'temperature_drift_count': temperature_drift_count, 
               'excessive_vibration_count': excessive_vibration_count,
               'voltage_drop_count': voltage_drop_count} 

    return anomalies, summary

def read_data_file(path):
    try:

        with open(path, 'r') as file:
            data = json.load(file)
            return data

    except FileNotFoundError:
        print(f"Error: File not found at '{path}'")
        return None

    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{path}'")
        return None


if __name__ == "__main__":
    
    output_dir = "test_data_reports"
    input_dir = "test_data"

    test_data = read_data_file("test_data.json")
    if test_data:
        anomalies, summary = analyze_test_data(test_data)

        print(f"\n\nSummary: {summary}\n")
        print(f"Anomalies found: {anomalies}\n")
    else:
        print("\nCould not process data file!")