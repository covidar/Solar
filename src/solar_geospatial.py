#!/usr/bin/env python3

"""Geospatial code."""

import logging
import utm
import osgeo.osr as osr

def get_utm_epsg_from_epsg(epsg_code, x, y):
    src = osr.SpatialReference()
    src.ImportFromEPSG(epsg_code)
    dst = osr.SpatialReference()
    dst.ImportFromEPSG(4326)
    ct = osr.CoordinateTransformation(src, dst)
    (lon, lat, _) = ct.TransformPoint(x, y)
    (easting, northing, zone_number, zone_letter) = utm.from_latlon(lat, lon)
    logging.info('E: %f N: %f Zone: %d Letter: %s' % (easting, northing, zone_number, zone_letter))
    if lat >= 0:
        utm_epsg = zone_number + 32600
    else:
        utm_epsg = zone_number + 32700
    logging.info('UTM epsg %d' % (utm_epsg))
    return utm_epsg

def is_valid_utm_epsg(epsg_code):
    """Is the UTM epsg code valid."""
    success = False

    # Note WGS84.
    # Northern UTM projections 32601 to 32660
    if epsg_code > 32600 and epsg_code < 32661:
        success = True
    # Southern UTM projections 32701 to 32760
    elif epsg_code > 32700 and epsg_code < 32761:
        success = True
    else:
        return False

    return success

def get_utm_zone_and_hemisphere(epsg_code):
    """Get the UTM zone number and hemispehere given the epsg code."""

    zone_number = None
    northern = None

    # Get the zone number and hemisphere
    if epsg_code > 32700 and epsg_code < 32761:
        zone_number = epsg_code - 32700
        northern = False
    if epsg_code > 32600 and epsg_code < 32661:
        zone_number = epsg_code - 32600
        northern = True

    return zone_number, northern

def get_lat_lon(epsg_code, easting, northing):
    """Get the latitude and longitude from UTM coordinates."""

    lat = None
    lon = None

    # Validate the epsg code.
    if is_valid_utm_epsg(epsg_code):

        # Get the zone and hemispehere
        (zone_number, northern) = get_utm_zone_and_hemisphere(epsg_code)

        # Get the latitude and longitude in degrees.
        if zone_number != None and northern != None:
            lat, lon = utm.to_latlon(easting, northing, zone_number, northern=northern)

    return lat, lon
