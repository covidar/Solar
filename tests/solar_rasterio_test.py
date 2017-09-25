#!/usr/bin/env python3

import logging
import os
import unittest

import solar_rasterio as sr

logging.basicConfig(filename='solar_rasterio_test.log', format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S", filemode='w', level=logging.DEBUG)

class TestRaster(unittest.TestCase):

    def setUp(self):
        self.patch = './tests/data/Patch_DEM.tif'
        self.lena = './tests/data/Lena.jpg'

    def test_open_image_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))

    def test_open_image_2(self):
        img = sr.SolarImage()
        self.assertFalse(img.open_image('dummy.txt'))

    def test_size_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        self.assertEqual(img.width(), 186)
        self.assertEqual(img.height(), 214)
        (height, width) = img.shape()
        self.assertEqual(width, 186)
        self.assertEqual(height, 214)

    def test_no_data_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        self.assertEqual(img.no_data(), None)

    def test_bands_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        self.assertEqual(img.bands(), 1)

    def test_bands_2(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.lena))
        self.assertEqual(img.bands(), 3)

    def test_get_bands_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        band = img.get_bands(1)
        (height, width) = band.shape
        self.assertEqual(width, 186)
        self.assertEqual(height, 214)

    def test_get_affine_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        affine = img.get_affine()
        self.assertAlmostEqual(affine[0], 1.0, 2)
        self.assertAlmostEqual(affine[1], 0.0, 2)
        self.assertAlmostEqual(affine[2], 554440, 2)
        self.assertAlmostEqual(affine[3], 0.0, 2)
        self.assertAlmostEqual(affine[4], -1.0, 2)
        self.assertAlmostEqual(affine[5], 4.15065e+06, 2)

    def test_get_epsg_code_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        self.assertEqual(img.get_epsg_code(), 32610)

    def test_get_centroid_ground(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        (gx, gy) = img.get_centroid_ground()
        self.assertAlmostEqual(gx, 554533)
        self.assertAlmostEqual(gy, 4150543)

    def test_get_avg_gsd_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        self.assertAlmostEqual(img.get_avg_gsd(), 1.0, 3)

    def test_padded_image_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        band = img.get_bands(1)
        (height, width) = img.shape()
        max_size = max(height, width)
        pad_rows = int((max_size - height) / 2.0)
        pad_cols = int((max_size - width) / 2.0)
        padded = sr.padded_image(band, pad_rows, pad_cols)
        (pad_width, pad_height) = padded.shape
        self.assertEqual(pad_width, 214)
        self.assertEqual(pad_height, 214)
        self.assertEqual(padded[0][0], -9999)
        self.assertNotEqual(padded[100][100], -9999)

    def test_rotate_image_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        band = img.get_bands(1)
        rotated = sr.rotate_image(band, 0, no_data=-9999)
        self.assertEqual(band[85][75], rotated[85][75])

    def test_rotate_image_2(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.patch))
        band = img.get_bands(1)
        padded = sr.padded_image(band, 0, 14)
        rotated = sr.rotate_image(padded, 90.0, no_data=-9999)
        self.assertAlmostEqual(padded[107][107], rotated[107][107], delta=1)
        self.assertAlmostEqual(padded[0][107], rotated[107][0], delta=1)

    def test_resample_image_1(self):
        src = './tests/data/pa_large_dsm_3_1.tif'
        dst = './tests/results/pa_large_dsm_3_1_1p0.tif'
        epsg = 32610
        resampled = sr.resample_image(src, dst, epsg, epsg, 1.0, no_data=-9999)
        self.assertTrue(resampled)
        avg_gsd = sr.get_gsd(dst)
        self.assertEqual(avg_gsd, 1.0)

    def test_clip_padded_image_1(self):
        img = sr.SolarImage()
        self.assertTrue(img.open_image(self.lena))
        band = img.get_bands(1)
        clip = sr.clip_padded_image(band, 10, 20)
        self.assertEqual(band[10][20], clip[0][0])        
        self.assertEqual(band[46][99], clip[36][79])        

    def test_get_epsg_1(self):
        (epsg, ground_x, ground_y, no_data) = sr.get_epsg(self.patch)
        print(epsg, ground_x, ground_y, no_data)

    def test_write_affine_1(self):
        filename = './tests/results/affine.tfw'
        affine = [0, 1, 4, 2, 3, 5]
        sr.write_affine(filename, affine)
        self.assertTrue(os.path.exists(filename))

if __name__ == '__main__':
    unittest.main()
