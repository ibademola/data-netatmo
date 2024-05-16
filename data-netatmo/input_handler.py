def get_user_inputs():
    # Accept user inputs for various parameters
    lat_ne = float(input("Enter lat_ne: "))
    lon_ne = float(input("Enter lon_ne: "))
    lat_sw = float(input("Enter lat_sw: "))
    lon_sw = float(input("Enter lon_sw: "))
    start_date_stamp = input("Enter start_date_stamp (yyyymmdd): ")
    start_time_stamp = input("Enter start_time_stamp (hhmm): ")
    end_date_stamp = input("Enter end_date_stamp (yyyymmdd): ")
    end_time_stamp = input("Enter end_time_stamp (hhmm): ")
    csv_file = input("Enter CSV file name: ")
    client_id = input("Enter client ID: ")
    client_secret = input("Enter client secret: ")
    refresh_token = input("Enter refresh token: ")

    return lat_ne, lon_ne, lat_sw, lon_sw, start_date_stamp, start_time_stamp, end_date_stamp, end_time_stamp, csv_file, client_id, client_secret, refresh_token
