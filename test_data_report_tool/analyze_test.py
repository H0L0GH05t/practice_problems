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
import os
import pandas as pd


def check_excessive_vibration(data_line, anomalies, excessive_vibration_count):
    '''
    Checks for excessive vibration based on if combined magnitude exceeds 10.0 at any point

    Takes in the current data_line from the current json file and counter and returns
    updated dictionary and count

    '''

    # check vibration against threshold
    magnitude = math.sqrt(data_line['vibration_x']**2 + data_line['vibration_y']**2)
    if magnitude > 10.0:
        # found excessive vibration, increment count and add info to list
        excessive_vibration_count += 1
        anomalies.append({'type': 'excessive_vibration', 
                              'timestamp': data_line['timestamp'], 
                              'details': f'Combined Magnitude: {magnitude}'})
    return anomalies, excessive_vibration_count


def check_temperature_drift(data_line, anomalies, temperature_drift_count, all_data):
    '''
    Checks for over a + or - 5 degrees C temperature shift over a sliding 60 second time window

    Takes in the current data_line from the current json file, counter, time window start, and all accumulated data
    and returns updated dictionary and count

    '''

    if len(all_data) > 1:
        df = pd.DataFrame(all_data)
        series = df['temperature']
        differences = series.rolling(window=2).apply(lambda x: x.iloc[-1] - x.iloc[0])
        differences.dropna()

        for diff in differences:
            if diff > 5 or diff < -5:
                temperature_drift_count += 1
                anomalies.append({'type': 'temperature_drift', 
                                  'timestamp': data_line['timestamp'], 
                                  'details': f'Temperature Changed by {diff} Degrees C'})
                break

        # TODO: check if 60 seconds has passed and reset window if so, currently 12 rows consecutively is 5 seconds each, so 12 for 60
        if len(all_data) > 12:
            all_data = []


    return anomalies, temperature_drift_count

def check_voltage_drop(data_line, anomalies, voltage_drop_count, previous_voltage, consecutive_lows):
    '''
    Checks for sustained voltage drop over 10 consecutive readings

    Takes in the current data_line from the current json file, relevant counters, and previous voltage
    and returns updated dictionary and counts

    '''

    # first data point, so save voltage and move on
    if previous_voltage == 0:
        previous_voltage = data_line['voltage']

    # check for low voltage, incrementing count
    elif previous_voltage < 4.5 and data_line['voltage'] < 4.5 and consecutive_lows < 10:
        consecutive_lows += 1
        previous_voltage = data_line['voltage']

    # check for hitting consecutive count, add anomaly
    elif previous_voltage < 4.5 and data_line['voltage'] < 4.5 and consecutive_lows > 10:
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
    '''
    Runs check functions for each anomaly type for each data_line in test_data

    Takes in test_data from the current json file, keeps track of counts and returns
    a dictionary of anomalies found and a summary dictionary with counts of anomaly types

    '''

    anomalies = []
    summary = {'temperature_drift_count': 0, 
               'excessive_vibration_count': 0,
               'voltage_drop_count': 0}

    temperature_drift_count = 0
    excessive_vibration_count = 0
    voltage_drop_count = 0

    all_data = []

    previous_voltage = 0
    consecutive_lows = 0

    # iterate test data
    for data_line in test_data:

        # Start keeping track of data for the window
        all_data.append(data_line)
        
        # check the window for temperature drift
        anomalies, temperature_drift_count = check_temperature_drift(data_line, anomalies, temperature_drift_count, all_data)

        anomalies, voltage_drop_count, previous_voltage, consecutive_lows = check_voltage_drop(data_line, anomalies, voltage_drop_count, previous_voltage, consecutive_lows)

        anomalies, excessive_vibration_count = check_excessive_vibration(data_line, anomalies, excessive_vibration_count)

    summary = {'temperature_drift_count': temperature_drift_count, 
               'excessive_vibration_count': excessive_vibration_count,
               'voltage_drop_count': voltage_drop_count} 

    return anomalies, summary

def read_data_file(path):
    '''
    Reads the file located at path and returns the data from it

    '''
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

def write_report_file(anomalies, summary, test_file, output_dir):
    '''
    Writes the resulting report data for a test_data file

    '''
    try:
        output_path = f"{test_file[:-5]}_SUMMARY.json"

        with open(path, 'w') as file:
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

    for root, dirs, test_files in os.walk(input_dir):
        for test_file in test_files:

            print(f'\nReading from file: {test_file} ---------------------')
            test_data = read_data_file(os.path.join(root, test_file))

            if test_data:
                anomalies, summary = analyze_test_data(test_data)

                # write_report_file(anomalies, summary, test_file, output_dir)

                print(f"\n\nSummary: {summary}\n")
                print(f"Anomalies found: {anomalies}\n")
                print(f"---------------------------------------------------------\n")
            else:
                print(f"\nCould not process data file {test_file}!")