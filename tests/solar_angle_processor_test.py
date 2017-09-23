#!/usr/bin/env python3

import os
import logging
import unittest
from datetime import datetime, date, time
import numpy as np
import pytz

import solar_utility as su
import solar_rasterio as sr
import solar_angle_processor as sa

logging.basicConfig(filename='solar_angle_processor_test.log', format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S", filemode='w', level=logging.DEBUG)

class TestAngleProcessor(unittest.TestCase):

    def setUp(self):
        pass

    def test_process_column_1(self):
        no_data = -9999
        col_data = su.create_image((50), no_data)
        angles = sa.process_column(col_data, no_data)
        size = angles.shape
        self.assertEqual(size[0], 50)
        unique_values = np.unique(angles)
        self.assertEqual(len(unique_values), 1)
        self.assertEqual(unique_values[0], no_data)

    def test_process_column_2(self):
        no_data = -9999
        col_data = su.create_image((50), 2)
        col_data[0] = 1
        angles = sa.process_column(col_data, no_data)
        size = angles.shape
        self.assertEqual(size[0], 50)
        self.assertEqual(angles[0], 45)

    def test_process_column_3(self):
        no_data = -9999
        col_data = su.create_image((50), 2)
        col_data[10] = 1
        angles = sa.process_column(col_data, no_data)
        size = angles.shape
        self.assertEqual(size[0], 50)
        self.assertEqual(angles[10], 45)

    def test_process_angles_1(self):
        no_data = -9999
        elevation = su.create_image((25, 5), 3.0)
        elevation[0][0] = 1.0
        elevation[0][1] = 2.0
        elevation[0][2] = 1.0
        elevation[0][3] = 2.0
        elevation[0][4] = 1.0
        angles = sa.process_angles(elevation, no_data)
        self.assertAlmostEqual(angles[0][0], 63.4349, delta=0.1)
        self.assertAlmostEqual(angles[0][1], 45, delta=0.1)
        self.assertAlmostEqual(angles[0][2], 63.4349, delta=0.1)
        self.assertAlmostEqual(angles[0][3], 45, delta=0.1)
        self.assertAlmostEqual(angles[0][4], 63.4349, delta=0.1)

    def test_process_angles_2(self):
        no_data = -9999
        col_data = su.create_image((25, 5), 3)
        col_data[0][0] = 1
        col_data[0][1] = 2
        col_data[0][2] = 1
        col_data[0][3] = 2
        col_data[0][4] = 1
        col_data[5][0] = 7
        col_data[5][1] = 7
        col_data[5][2] = 7
        col_data[5][3] = 7
        col_data[5][4] = 7
        angles = sa.process_angles(col_data, no_data)
        self.assertAlmostEqual(angles[0][0], 63.4349, delta=0.1)
        self.assertAlmostEqual(angles[0][1], 45, delta=0.1)
        self.assertAlmostEqual(angles[0][2], 63.4349, delta=0.1)
        self.assertAlmostEqual(angles[0][3], 45, delta=0.1)
        self.assertAlmostEqual(angles[0][4], 63.4349, delta=0.1)
        self.assertAlmostEqual(angles[4][0], 75.9637, delta=0.1)
        self.assertAlmostEqual(angles[4][1], 75.9637, delta=0.1)
        self.assertAlmostEqual(angles[4][2], 75.9637, delta=0.1)
        self.assertAlmostEqual(angles[4][3], 75.9637, delta=0.1)
        self.assertAlmostEqual(angles[4][4], 75.9637, delta=0.1)

    def test_process_angles_3(self):
        no_data = -9999
        img = sr.SolarImage()
        filename = './tests/data/Patch_DEM.tif'
        self.assertTrue(img.open_image(filename))
        band = img.get_bands(1)
        (band_height, band_width) = band.shape
        angles = sa.process_angles(band, no_data)
        (angle_height, angle_width) = angles.shape
        self.assertEqual(angle_height, band_height)
        self.assertEqual(angle_width, band_width)

    def test_interpolate_1(self):
        local_timezone = pytz.timezone('US/Pacific')
        d = date(2017, 7, 1)
        t = time(4, 48, 0, 0, local_timezone)
        sr_dt = datetime.combine(d, t)
        t = time(4, 54, 0, 0, local_timezone)
        ss_dt = datetime.combine(d, t)
        sr_secs = su.get_seconds_from_datetime(sr_dt)
        ss_secs = su.get_seconds_from_datetime(ss_dt)
        xp = [-1.1215961463098312, 0.19803995875409597]
        yp = [sr_secs, ss_secs]
        secs = sa.interpolate(xp, yp, True)
        real_time = time(4, 51, 0, 0, local_timezone)
        real_dt = datetime.combine(d, real_time)
        real_secs = su.get_seconds_from_datetime(real_dt)
        self.assertAlmostEqual(secs, real_secs, delta=180)

    def test_compute_sunrise_1(self):
        size = 5
        no_data = -9999
        prior = su.create_image((size, size), -3)
        now = su.create_image((size, size), 3)
        sunrise = su.create_image((size, size), no_data)
        sunset = su.create_image((size, size), no_data)
        prior_secs = 500
        now_secs = 506
        sunrise = sa.compute_sunrise(prior, now, prior_secs, now_secs, no_data, sunrise, sunset)
        self.assertEqual(sunrise[3][3], 503)

    def test_compute_sunrise_2(self):
        size = 5
        no_data = -9999
        prior = su.create_image((size, size), 3)
        now = su.create_image((size, size), 6)
        sunrise = su.create_image((size, size), no_data)
        sunset = su.create_image((size, size), no_data)
        prior_secs = 500
        now_secs = 506
        sunrise = sa.compute_sunrise(prior, now, prior_secs, now_secs, no_data, sunrise, sunset)
        self.assertEqual(sunrise[3][3], no_data)

    def test_compute_sunrise_3(self):
        size = 5
        no_data = -9999
        prior = su.create_image((size, size), -6)
        now = su.create_image((size, size), -3)
        sunrise = su.create_image((size, size), no_data)
        sunset = su.create_image((size, size), no_data)
        prior_secs = 500
        now_secs = 506
        sunrise = sa.compute_sunrise(prior, now, prior_secs, now_secs, no_data, sunrise, sunset)
        self.assertEqual(sunrise[3][3], no_data)

    def test_compute_sunset_1(self):
        size = 5
        no_data = -9999
        prior = su.create_image((size, size), 3)
        now = su.create_image((size, size), -3)
        sunset = su.create_image((size, size), no_data)
        prior_secs = 600
        now_secs = 606
        sunset = sa.compute_sunset(prior, now, prior_secs, now_secs, no_data, sunset)
        self.assertEqual(sunset[3][3], 603)

    def test_compute_sunset_2(self):
        size = 5
        no_data = -9999
        prior = su.create_image((size, size), 6)
        now = su.create_image((size, size), 3)
        sunset = su.create_image((size, size), no_data)
        prior_secs = 600
        now_secs = 606
        sunset = sa.compute_sunset(prior, now, prior_secs, now_secs, no_data, sunset)
        self.assertEqual(sunset[3][3], no_data)

    def test_compute_sunset_3(self):
        size = 5
        no_data = -9999
        prior = su.create_image((size, size), -3)
        now = su.create_image((size, size), -6)
        sunrise = su.create_image((size, size), no_data)
        sunset = su.create_image((size, size), no_data)
        prior_secs = 600
        now_secs = 606
        sunrise = sa.compute_sunrise(prior, now, prior_secs, now_secs, no_data, sunrise, sunset)
        self.assertEqual(sunrise[3][3], no_data)

    def test_load_surface_1(self):
        filename = './tests/data/Patch_DEM.tif'
        (success, _, metadata) = sa.load_surface(filename)
        self.assertTrue(success)
        #            0         1         2       3      4    5    6    7
        #metadata = [pad_rows, pad_cols, height, width, lat, lon, gsd, no_data]
        self.assertEqual(metadata[0], 35)
        self.assertEqual(metadata[1], 49)
        self.assertEqual(metadata[2], 214)
        self.assertEqual(metadata[3], 186)
        self.assertAlmostEqual(metadata[4], 37.50020658144657)
        self.assertAlmostEqual(metadata[5], -122.38304297806413)
        self.assertEqual(metadata[6], 1.0)
        self.assertEqual(metadata[7], -9999)

    def test_load_surface_2(self):
        filename = './tests/data/dummy.tif'
        (success, _, _) = sa.load_surface(filename)
        self.assertFalse(success)

    def test_process_surface_1(self):
        filename = './tests/data/Patch_DEM.tif'
        (success, surface, metadata) = sa.load_surface(filename)
        self.assertTrue(success)
        time_zone = 'US/Pacific'
        year = 2017
        month = 7
        day = 1
        increments = 1
        local_date = date(year, month, day)
        lat = metadata[4]
        lon = metadata[5]
        (sunrise, sunset) = su.get_sun_rise_set(year, month, day, time_zone, lat, lon)
        output_path = './tests/results'
        metadata.append(time_zone)
        metadata.append(increments)
        metadata.append(output_path)
        metadata.append(filename)
        radiation = False
        tiff = False
        workers = 1
        sa.process_surface(surface, metadata, local_date, sunrise, sunset, radiation, tiff, workers)
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-07-01_light_perc.png'))

    def test_process_surface_2(self):
        filename = './tests/data/Patch_DEM.tif'
        (success, surface, metadata) = sa.load_surface(filename)
        self.assertTrue(success)
        time_zone = 'US/Pacific'
        year = 2017
        month = 8
        day = 2
        increments = 1
        local_date = date(year, month, day)
        lat = metadata[4]
        lon = metadata[5]
        (sunrise, sunset) = su.get_sun_rise_set(year, month, day, time_zone, lat, lon)
        output_path = './tests/results'
        metadata.append(time_zone)
        metadata.append(increments)
        metadata.append(output_path)
        metadata.append(filename)
        radiation = False
        tiff = True
        workers = 1
        sa.process_surface(surface, metadata, local_date, sunrise, sunset, radiation, tiff, workers)
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-08-02_light_perc.png'))
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-08-02_light_perc.tif'))
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-08-02_light_secs.tif'))
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-08-02_sunrise.tif'))
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-08-02_sunset.tif'))

    def test_process_surface_3(self):
        filename = './tests/data/Patch_DEM.tif'
        (success, surface, metadata) = sa.load_surface(filename)
        self.assertTrue(success)
        time_zone = 'US/Pacific'
        year = 2017
        month = 9
        day = 3
        increments = 1
        local_date = date(year, month, day)
        lat = metadata[4]
        lon = metadata[5]
        (sunrise, sunset) = su.get_sun_rise_set(year, month, day, time_zone, lat, lon)
        output_path = './tests/results'
        metadata.append(time_zone)
        metadata.append(increments)
        metadata.append(output_path)
        metadata.append(filename)
        radiation = True
        tiff = False
        workers = 1
        sa.process_surface(surface, metadata, local_date, sunrise, sunset, radiation, tiff, workers)
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-09-03_light_perc.png'))
        self.assertTrue(os.path.exists('./tests/results/Patch_DEM_2017-09-03_radiation.tif'))

    def test_clean_given_surface_1(self):
        size = 10
        no_data = -9999
        data = su.create_image((size, size), 1)
        surface = su.create_image((size, size), no_data)
        new_data = sa.clean_given_surface(surface, data, no_data)
        for row in range(size):
            for col in range(size):
                self.assertEqual(new_data[row][col], no_data)

    def test_clean_given_surface_2(self):
        size = 10
        no_data = -9999
        data = su.create_image((size, size), 2)
        surface = su.create_image((size, size), no_data)
        surface[5][6] = 1
        new_data = sa.clean_given_surface(surface, data, no_data)
        for row in range(size):
            for col in range(size):
                if row == 5 and col == 6:
                    self.assertEqual(new_data[row][col], 2)
                else:
                    self.assertEqual(new_data[row][col], no_data)

    def test_clean_given_surface_3(self):
        size = 10
        no_data = -9999
        data = su.create_image((size, size), 1)
        surface = su.create_image((size+1, size), no_data)
        new_data = sa.clean_given_surface(surface, data, no_data)
        for row in range(size):
            for col in range(size):
                self.assertEqual(new_data[row][col], data[row][col])

    def test_preprocess_surface_1(self):
        filename = './tests/data/pa_large_dsm_3_1.tif'
        output_path = './tests/results'
        (resampled, surface_tmpname) = sa.preprocess_surface(filename, output_path, 5)
        self.assertTrue(resampled)
        self.assertTrue(os.path.exists(surface_tmpname))

    def test_preprocess_surface_2(self):
        filename = './tests/data/Patch_DEM_wgs84.tif'
        output_path = './tests/results'
        (resampled, surface_tmpname) = sa.preprocess_surface(filename, output_path, 5)
        self.assertTrue(resampled)
        self.assertTrue(os.path.exists(surface_tmpname))
