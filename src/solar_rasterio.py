#!/usr/bin/env python3

"""Raster code."""

import logging
import numpy as np
import osgeo.gdal as gdal
import rasterio
from skimage.transform import rotate

class SolarImage:
    """Solar image class."""

    def __init__(self):
        self.img = None

    def open_image(self, file_name, mode='r'):
        """Open an image."""
        try:
            self.img = rasterio.open(file_name, mode)
            if self.img != None:
                return True
        except OSError:
            # Consider logging!
            return False
        else:
            return False

    def close_image(self):
        """Close the image."""
        self.img.close

    def width(self):
        """Get the image width."""
        return self.img.width

    def height(self):
        """Get the image height."""
        return self.img.height

    def shape(self):
        """Get the shape!"""
        return self.img.shape

    def no_data(self):
        """Get the no data value."""
        return self.img.nodata

    def bands(self):
        """Get the number of bands."""
        return self.img.count

    def profile(self):
        """Get the profile."""
        return self.img.profile

    def get_bands(self, bands):
        """Get the bands in an image."""
        return self.img.read(bands)

    def get_affine(self):
        """Get the affine transformation."""
        return self.img.affine

    def get_epsg_code(self):
        """Get the epsg code."""
        crs = self.img.crs
        epsg = crs['init']
        epsg_code = int(epsg[5:])
        return epsg_code

    def get_centroid_ground(self):
        """Get the center of the image in ground coordinates."""
        half_width = self.img.width / 2.0
        half_height = self.img.height / 2.0
        affine = self.get_affine()
        ground_x = affine[2] + affine[0] * half_width
        ground_y = affine[5] + affine[4] * half_height
        return ground_x, ground_y

    def get_avg_gsd(self):
        """Get the average GSD."""
        affine = self.img.affine
        return (affine[0] - affine[4]) / 2.0

def padded_image(image, pad_rows, pad_cols, no_data=-9999):
    """Pad an image with cols and rows."""
    # Get the current size.
    (height, width) = image.shape

    # Get the new size.
    new_width = width + 2 * pad_cols
    new_height = height + 2 * pad_rows

    # Get the padded image.
    pad_image = np.ones((new_height, new_width))
    pad_image *= no_data

    # Place the dem in the center.
    pad_image[pad_rows:pad_rows + height, pad_cols:pad_cols + width] = image

    return pad_image.copy()

def clip_padded_image(image, pad_rows, pad_cols, no_data=-9999):
    """Clip a padded image."""
    # Get the current size.
    (height, width) = image.shape

    # Get the new size.
    new_width = width - 2 * pad_cols
    new_height = height - 2 * pad_rows

    # Get the clipped image.
    clipped_image = np.ones((new_height, new_width))
    clipped_image *= no_data

    # Clip the image.
    clipped_image = image[pad_rows:pad_rows + new_height, pad_cols:pad_cols + new_width]

    return clipped_image.copy()

def rotate_image(image, rotation_angle, no_data=-9999):
    """
    Rotate an image about an angle.
    Rotation angle in degrees in counter-clockwise direction.
    """
    rotated_image = rotate(image, rotation_angle, order=0, cval=no_data,
                           resize=False, preserve_range=True)
    return rotated_image.copy()

def resample_image(src, dst, srcEpsg, dstEpsg, gsd, no_data):
    """Resample the image using GDAL."""
    try:
        logging.info('EPSG %d to %d' % (srcEpsg, dstEpsg))
        warp_opt = gdal.WarpOptions(xRes=gsd, yRes=gsd, srcNodata=no_data,
            dstNodata=no_data, srcSRS='EPSG:' + str(srcEpsg), dstSRS='EPSG:' + str(dstEpsg))
        gdal.Warp(destNameOrDestDS=dst, srcDSOrSrcDSTab=src, options=warp_opt)
    except IOError:
        logging.error('Problem resampling %s', src)
        return False
    return True

def get_gsd(file_name):
    """Get the GSD from an image."""
    avg_gsd = 0.0
    img = SolarImage()
    if img.open_image(file_name):
        avg_gsd = img.get_avg_gsd()
        img.close_image()
    return avg_gsd

def get_epsg(file_name):
    """Get the epsg code."""
    epsg = None
    ground_x = 0
    ground_y = 0
    img = SolarImage()
    if img.open_image(file_name):
        epsg = img.get_epsg_code()
        (ground_x, ground_y) = img.get_centroid_ground()
        no_data = img.no_data()
        img.close_image()
    return epsg, ground_x, ground_y, no_data

def write_output(name, img, profile, dn_type=rasterio.float64):
    """Write some output."""
    new_profile = profile
    new_profile.update(dtype=dn_type)
    with rasterio.open(name, 'w', **new_profile) as dst:
        dst.write(img, 1)

def write_affine(name, affine):
    """Write a TIFF world file."""
    with open(name, 'w') as worldfile:
        worldfile.write('%f\n' % affine[0])
        worldfile.write('%f\n' % affine[1])
        worldfile.write('%f\n' % affine[3])
        worldfile.write('%f\n' % affine[4])
        worldfile.write('%f\n' % affine[2])
        worldfile.write('%f\n' % affine[5])