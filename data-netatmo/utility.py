import csv
import requests
import time
from datetime import datetime


start_time = time.time()

def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)

def convert_to_unix_timestamp(date_string, time_string):
    try:
        # Parse the date and time strings
        date_obj = datetime.strptime(date_string, '%Y%m%d')
        time_obj = datetime.strptime(time_string, '%H%M')
        
        # Combine date and time
        datetime_obj = datetime(date_obj.year, date_obj.month, date_obj.day, time_obj.hour, time_obj.minute)
        
        # Convert to UNIX timestamp
        timestamp = int(datetime_obj.timestamp())
        return timestamp
    except ValueError:
        print("Error: Invalid input format. Please provide date in 'yyyymmdd' and time in 'hhmm' format.")
        return None


def get_access_token(client_id, client_secret, refresh_token):
    # URL for token endpoint
    token_url = "https://api.netatmo.com/oauth2/token"

    # Parameters for token request
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }

    # Send POST request to get access token
    response = requests.post(token_url, data=params)

    # Check if request was successful
    if response.status_code == 200:
        # Parse JSON response
        token_data = response.json()
        # Access token
        access_token = token_data["access_token"]
        return access_token
    else:
        print("Error:", response.status_code, response.text)
        return None

def get_ids(access_token, lat_ne, lon_ne, lat_sw, lon_sw):
    params = {
        'access_token': access_token,
        'lat_ne' : lat_ne,
        'lon_ne' : lon_ne,
        'lat_sw' : lat_sw,
        'lon_sw' : lon_sw,
    }

    ids = {}
    NoResponse = True
    retry_count = 0
    while NoResponse:
        #try to get stations in given region, 5 attempts before moving on to next area
        try:
            #try to get stations
            response = requests.post("https://api.netatmo.com/api/getpublicdata", params=params)
            response.raise_for_status()
            data = response.json()["body"]
            for station in data:
            #find each value for each station
                _id = station['_id']
                mod = [n for n in station['modules'] if n.startswith('02:')]
                location = station['place']['location']
                altitude = station['place']['altitude']
                if 'city' in station['place'].keys():
                    city = station['place']['city']
                else:
                    city = 'no city'
                ids[_id] = ({'module_name':mod, 'location':location, 'altitude':altitude,
                             'city':city, 'full_modules':station['modules']})

            #Checking that some data has been returned
            if len(ids) == 0:
            #if everything works but we have no data returned in the given box, raise
                raise NameError('length')                
        except requests.exceptions.HTTPError as error:
            #if there's an error, try four more times before moving on
            print(error.response.status_code, error.response.text)
            if retry_count < 5:
                retry_count += 1
            else:
                return({})
        except NameError:
            if retry_count < 5:
                retry_count += 1
            else:
                return({})
        else:
            NoResponse = False
            return(ids)

def save_netatmo_data_to_csv(ids, csv_file):
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['MAC_address', 'module_name', 'latitude', 'longitude', 'altitude', 'city', 'full_modules'])
        for mac_address, value in ids.items():
            latitude, longitude = value['location']
            writer.writerow([mac_address, value['module_name'], latitude, longitude, value['altitude'], value['city'], value['full_modules']])
    return csv_file

def get_historical_measurements(access_token, device_id, module_id, scale, types, date_begin, date_end, limit=1024):
    url = "https://api.netatmo.net/api/getmeasure"
    
    params = {
        'access_token': access_token,
        'device_id': device_id,
        'module_id': module_id,
        'scale': scale,
        'type': types,
        'date_begin': date_begin,
        'date_end': date_end,
        'limit': limit
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def load_device_and_module_ids_from_csv(csv_file):
    device_module_ids = []
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            device_id = row[0]
            module_id = row[1].strip("[]'")  # Remove square brackets and single quotes
            device_module_ids.append((device_id, module_id))
    return device_module_ids

def save_measurements_to_csv(measurements, device_id, module_id):
    # Remove ":" from device and module IDs for filename
    device_id_filename = device_id.replace(":", "")
    module_id_filename = module_id.replace(":", "")
    
    filename = f'{device_id_filename}_{module_id_filename}_measurements.csv'
    
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['acquisition_time', 'temperature', 'humidity', 'pressure']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Skip writing header if file is not empty
        if csvfile.tell() == 0:
            writer.writeheader()

        acquisition_time = measurements['body'][0]['beg_time']
        step_time = 86400
        # step_time = measurements['body'][0]['step_time']
        for entry in measurements['body']:
            for value in entry['value']:
                row = {
                    'acquisition_time': datetime.utcfromtimestamp(acquisition_time).strftime('%Y%m%d%H%M'),
                    'temperature': value[0],
                    'humidity': value[1],
                    'pressure': value[2]
                }
                writer.writerow(row)
                acquisition_time += step_time

def get_historical_measurements_batch(access_token, device_id, module_id, scale, types, date_begin, date_end, limit=1024):
    all_measurements = []

    while date_begin < date_end:
        measurements = get_historical_measurements(access_token, device_id, module_id, scale, types, date_begin, date_end, limit)
        if measurements is None or "body" not in measurements or not measurements["body"]:
            # No more data available or an error occurred, stop the loop
            break

        # Extract the last timestamp from the received data
        last_timestamp = measurements["body"][-1]["beg_time"]
        
        # Append the measurements to the list
        all_measurements.extend(measurements["body"])

        # Update date_begin to fetch the next batch of data
        date_begin = last_timestamp + 86400
        # date_begin = last_timestamp + measurements["body"][-1]["step_time"]

        # Save measurements to CSV file
        save_measurements_to_csv(measurements, device_id, module_id)

        # Introduce a delay to avoid hitting rate limits
        time.sleep(1)

    return all_measurements
