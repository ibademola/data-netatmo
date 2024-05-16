import csv
import time
from utility import (get_access_token, get_ids, save_netatmo_data_to_csv,
                     load_device_and_module_ids_from_csv,
                     get_historical_measurements,
                     convert_to_unix_timestamp,
                     get_historical_measurements_batch,
                     save_measurements_to_csv,
                     format_time)
from input_handler import get_user_inputs

start_time = time.time()

# Get user inputs
(lat_ne, lon_ne, lat_sw, lon_sw, start_date_stamp, start_time_stamp,
 end_date_stamp, end_time_stamp, csv_file, client_id, client_secret,
 refresh_token) = get_user_inputs()

# Get access token
access_token = get_access_token(client_id, client_secret, refresh_token)

# Get IDs
ids = get_ids(access_token, lat_ne, lon_ne, lat_sw, lon_sw)
save_netatmo_data_to_csv(ids, csv_file)

# Load device IDs and module IDs from the CSV file
device_module_ids = load_device_and_module_ids_from_csv(csv_file)

# Iterate through each device ID and module ID pair
for device_id, module_id in device_module_ids:
    scale = "1day"  # Change according to your requirement
    types = "Temperature,Humidity,Pressure"  # Add or remove types as needed
    date_begin = convert_to_unix_timestamp(start_date_stamp, start_time_stamp)  # Start timestamp
    date_end = convert_to_unix_timestamp(end_date_stamp, end_time_stamp)  # End timestamp, set to "last" to retrieve only the last measurement
    limit = 1024  # Default limit

    # Fetch historical measurements for the current device ID and module ID pair
    measurements = get_historical_measurements_batch(access_token, device_id, module_id, scale, types, date_begin, date_end, limit)
    print(f'--------data for {device_id, module_id} completely downloaded----------')

processing_time_seconds = time.time() - start_time
processing_time_formatted = format_time(processing_time_seconds)

print("Data for all devices downloaded successfully.", f"Processing time: {processing_time_formatted}")
