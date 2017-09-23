#!/usr/bin/env python3

import unittest

import os
import numpy as np
from datetime import datetime, date, time
import pytz
import skimage.io as io

from solar_utility import get_seconds_from_datetime, get_time_from_seconds, get_sun_rise_set, create_image, get_processing_times, get_datetime, combine_datetime, log

logging.basicConfig(filename='solar_utility_test.log', format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S", filemode='w', level=logging.DEBUG)

class TestUtility(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_seconds_from_datetime_1(self):
        local_timezone = pytz.timezone('US/Pacific')
        d = date(2017, 6, 29)
        t = time(1, 0, 0, 0, local_timezone)
        dt = datetime.combine(d, t)
        self.assertEquals(get_seconds_from_datetime(dt), 3600)

    def test_get_seconds_from_datetime_2(self):
        local_timezone = pytz.timezone('US/Pacific')
        d = date(2017, 6, 29)
        t = time(1, 1, 20, 0, local_timezone)
        dt = datetime.combine(d, t)
        self.assertEquals(get_seconds_from_datetime(dt), 3680)

    def test_get_time_from_seconds_1(self):
        (hour, mins, secs) = get_time_from_seconds(3680)
        self.assertEquals(hour, 1)
        self.assertEquals(mins, 1)
        self.assertEquals(secs, 20)

    def test_get_sun_rise_set_1(self):
        # Sunnyvale!
        lat = 37.4041091
        lon = -122.0098641
        (sunrise, sunset) = get_sun_rise_set(2017, 7, 1, 'US/Pacific', lat, lon)
        # Good to minutes from NOAA.
        self.assertEquals(sunrise.hour, 5)
        self.assertEquals(sunrise.minute, 3)
        self.assertEquals(sunset.hour, 19)
        self.assertEquals(sunset.minute, 34)

    def test_create_image_1(self):
        test_image = create_image((15, 10), 10)
        (height, width) = test_image.shape
        self.assertEquals(height, 15)
        self.assertEquals(width, 10)
        self.assertEquals(test_image.dtype, 'float64')
        self.assertEquals(test_image[5][5], 10)

    def test_create_image_2(self):
        test_image = create_image((10, 15), 0)
        (height, width) = test_image.shape
        self.assertEquals(height, 10)
        self.assertEquals(width, 15)
        self.assertEquals(test_image.dtype, 'float64')
        self.assertEquals(test_image[5][5], 0)

    def test_create_image_3(self):
        test_image = create_image((20, 15), 3, dtype=np.uint8)
        (height, width) = test_image.shape
        self.assertEquals(height, 20)
        self.assertEquals(width, 15)
        self.assertEquals(test_image.dtype, 'uint8')
        self.assertEquals(test_image[10][10], 3)

    def test_create_image_4(self):
        no_data = -9999
        test_image = create_image((20, 1), no_data)
        (height, width) = test_image.shape
        self.assertEquals(height, 20)
        self.assertEquals(width, 1)
        self.assertEquals(test_image[10][0], no_data)

    def test_create_dem_1(self):
        width = 22
        height = 22
        dem = create_image((height+1, width+1), -10)
        for i in range(1, height, 2):
            for j in range(1, width, 2):
                dem[i][j] = 10
        for i in range(3, height, 2):
            for j in range(3, width, 2):
                dem[i][j] = 10

        name = os.path.join('./tests/data/', 'DEM_test.tif')
        io.imsave(name, dem)

    def test_get_processing_times_1(self):
        local_timezone = pytz.timezone('US/Pacific')
        d = date(2017, 7, 1)
        t = time(4, 0, 0, 0, local_timezone)
        sr_dt = datetime.combine(d, t)
        t = time(5, 0, 0, 0, local_timezone)
        ss_dt = datetime.combine(d, t)
        increments = 0
        times = get_processing_times(sr_dt, ss_dt, increments)
        self.assertEquals(len(times), 2)
        self.assertEquals(times[0], 14400)
        self.assertEquals(times[1], 18000)

    def test_get_processing_times_2(self):
        local_timezone = pytz.timezone('US/Pacific')
        d = date(2017, 7, 1)
        t = time(4, 0, 0, 0, local_timezone)
        sr_dt = datetime.combine(d, t)
        t = time(6, 0, 0, 0, local_timezone)
        ss_dt = datetime.combine(d, t)
        increments = 1
        times = get_processing_times(sr_dt, ss_dt, increments)
        self.assertEquals(len(times), 3)
        self.assertEquals(times[0], 14400)
        self.assertEquals(times[1], 18000)
        self.assertEquals(times[2], 21600)

    def test_combine_datetime_1(self):
        time_zone = 'US/Pacific'
        year = 2017
        month = 2
        day = 1
        local_date = date(2017, 2, 1)
        hour = 12
        mins = 13
        secs = 15
        ldt = combine_datetime(local_date, hour, mins, secs, time_zone)
        self.assertEquals(ldt.year, year)
        self.assertEquals(ldt.month, month)
        self.assertEquals(ldt.day, day)
        self.assertEquals(ldt.hour, hour)
        self.assertEquals(ldt.minute, mins)
        self.assertEquals(ldt.second, secs)
        print(ldt.tzname)

    def test_log_1(self):
        log('debug', 'debug')
        log('debug', 'debug1', stdout=True)
        log('info', 'info')
        log('warn', 'warn')
        log('error', 'error')

if __name__ == '__main__':
    unittest.main()