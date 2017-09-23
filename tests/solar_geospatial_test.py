#!/usr/bin/env python3

import unittest
from solar_geospatial import is_valid_utm_epsg, get_utm_zone_and_hemisphere, get_lat_lon, get_utm_epsg_from_epsg
 
 logging.basicConfig(filename='solar_geospatial_test.log', format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S", filemode='w', level=logging.DEBUG)

class TestGeospatial(unittest.TestCase):
 
    def setUp(self):
        pass
 
    def test_valid_epsg_1(self):
        self.assertTrue(is_valid_utm_epsg(32601))

    def test_valid_epsg_2(self):
        self.assertTrue(is_valid_utm_epsg(32731))
 
    def test_valid_epsg_3(self):
        self.assertFalse(is_valid_utm_epsg(4236))

    def test_valid_epsg_4(self):
        self.assertFalse(is_valid_utm_epsg(32600))

    def test_valid_epsg_5(self):
        self.assertFalse(is_valid_utm_epsg(32761))
 
    def test_get_utm_zone_and_hemisphere_1(self):
        (zone_number, northern) = get_utm_zone_and_hemisphere(32759)
        self.assertEqual(zone_number, 59)
        self.assertFalse(northern)

    def test_get_utm_zone_and_hemisphere_2(self):
        (zone_number, northern) = get_utm_zone_and_hemisphere(32613)
        self.assertEqual(zone_number, 13)
        self.assertTrue(northern)

    def test_get_utm_zone_and_hemisphere_3(self):
        (zone_number, northern) = get_utm_zone_and_hemisphere(2003)
        self.assertEqual(zone_number, None)
        self.assertEqual(northern, None)

    def test_get_lat_lon_1(self):
        (lat, lon) = get_lat_lon(32638, 444160, 3688032)
        self.assertAlmostEqual(lat, 33.33, places=3)
        self.assertAlmostEqual(lon, 44.4, places=3)

    def test_get_lat_lon_2(self):
        (lat, lon) = get_lat_lon(4356, 444160, 3688032)
        self.assertEqual(lat, None)
        self.assertEqual(lon, None)

    def test_get_lat_lon_3(self):
        (lat, lon) = get_lat_lon(32753, 462371, 6338917)
        self.assertAlmostEqual(lat, -33.0877144, places=3)
        self.assertAlmostEqual(lon, 134.5967937, places=3)

    def test_get_utm_from_epsg_1(self):
        lat = 37.42104680
        lon = -122.11992745
        utm_epsg = get_utm_epsg_from_epsg(4326, lon, lat)
        self.assertEqual(utm_epsg, 32610)

    def test_get_utm_from_epsg_2(self):
        lat = -37.42104680
        lon = -122.11992745
        utm_epsg = get_utm_epsg_from_epsg(4326, lon, lat)
        self.assertEqual(utm_epsg, 32710)

if __name__ == '__main__':
    unittest.main()