from datetime import datetime
import time
import pytz

def has_expired(expiry: int):
    return expiry <= int(round(time.time() * 1000))


def get_current_timestamp():
    return int(round(time.time() * 1000))


def get_current_date_time():
    return datetime.now()

def get_utc_timestamp(minute,hour,day,month,year):
    """
    Generate UTC Timestamp based on minute,hour , day , month and year
    """
    start_datetime = datetime(year, month, day, hour,minute)
    utc_timezone = pytz.timezone('UTC')
    start_datetime_utc = utc_timezone.localize(start_datetime)
    timestamp = start_datetime_utc.timestamp()
    return timestamp

def timestamp_to_time(timestamp):
    """
    UTC Timestamp to UTC time
    """
    utc_timezone = pytz.timezone('UTC')
    datetime_utc = datetime.fromtimestamp(timestamp, tz=utc_timezone)
    return datetime_utc.strftime("%Y-%m-%d %H:%M:%S.%f%z")

def calculate_time_difference_in_minutes(timestamp1, timestamp2):
    """
        To calculate the difference between timestamps and return in minutes
    """
    difference_in_milliseconds = abs(timestamp1 - timestamp2)
    difference_in_minutes = difference_in_milliseconds / (1000 * 60)
    return difference_in_minutes