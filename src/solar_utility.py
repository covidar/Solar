#!/usr/bin/env python3

"""Utility functions."""

import logging
from datetime import datetime, date, time
import numpy as np
from pysolar.util import get_sunrise_sunset
import pytz

def get_datetime(year, month, day, hour, time_zone):
    """ Get the datetime for the local timezone."""
    local_timezone = pytz.timezone(time_zone)
    local_date = date(year, month, day)
    local_time = time(hour, 0, 0, 0, local_timezone)
    local_date_time = datetime.combine(local_date, local_time)
    return local_date_time

def combine_datetime(local_date, hour, mins, secs, time_zone):
    """ Get the datetime for the local timezone."""
    local_timezone = pytz.timezone(time_zone)
    microsecond = 0
    local_time = time(hour, mins, secs, microsecond, local_timezone)
    local_date_time = datetime.combine(local_date, local_time)
    return local_date_time

def get_seconds_from_datetime(date_time):
    """Convert datetime into the number seconds in a day."""
    return date_time.hour * 3600 + date_time.minute * 60 + date_time.second

def get_time_from_seconds(secs):
    """Get the hours, minutes and seconds from the number of seconds in the day."""
    hour = int(secs / 3600)
    secs = secs - (hour * 3600)
    mins = int(secs / 60)
    secs = secs - (mins * 60)
    return hour, mins, secs

def get_sun_rise_set(year, month, day, time_zone, lat, lon):
    """Get the sunrise and sunset given the day and position."""
    # Get the date time for noon.
    hour = 12
    local_date_time = get_datetime(year, month, day, hour, time_zone)

    # Get the sunrise and sunset data for the day.
    sunrise, sunset = get_sunrise_sunset(lat, lon, local_date_time)

    return sunrise, sunset

def create_image(shape, value, dtype=np.float):
    """Create an image with a set size and set to a value."""
    ele = None
    if value != 0:
        ele = np.ones((shape), dtype)
        ele *= value
    else:
        ele = np.zeros((shape), dtype)
    return ele

def get_processing_times(sunrise, sunset, increments):
    """Create a list of processing times from sunset to sunrise."""
    times = []

    # Get the begining and the end.
    sunset_secs = get_seconds_from_datetime(sunset)
    sunrise_secs = get_seconds_from_datetime(sunrise)

    times.append(sunrise_secs)
    if increments == 0:
        times.append(sunset_secs)
    else:
        delta = sunset_secs - sunrise_secs
        increment_value = delta / float(increments+1)
        for inc in range(increments):
            times.append(sunrise_secs + (inc + 1) * increment_value)
        times.append(sunset_secs)

    return times

def log(level, log_message, stdout=False):
    if level == 'debug':
        logging.debug(log_message)
    if level == 'info':
        logging.info(log_message)
    if level == 'warn':
        logging.warn(log_message)
    if level == 'error':
        logging.error(log_message)

    if stdout:
        print(log_message)