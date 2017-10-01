#!/usr/bin/env python3

"""Angle processing."""

import matplotlib
matplotlib.use('Agg')

import concurrent.futures
import logging
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import tempfile
import queue
import warnings

# Solar installed.
from pysolar.solar import get_azimuth, get_altitude, radiation
from tqdm import tqdm

# Solar defined code.
import solar_geospatial as sg
import solar_rasterio as sr
import solar_utility as su

warnings.filterwarnings("ignore")

# Required to sort by the first value, e.g. tmp[0]
q = queue.PriorityQueue()

def process_column(col_data, no_data):
    """Process a column returning an array of angles."""

    # Get the length of the array.
    length = len(col_data)

    # Create a bucket for the results array.
    result = su.create_image((length), no_data)

    # Filter the no data values and record the position.
    elevation = []
    position = []
    for indx in range(length):
        if col_data[indx] != no_data:
            elevation.append(col_data[indx])
            position.append(float(indx))
 
    # We have nothing to do!
    if len(elevation) <= 1:
        logging.debug('Not enough elevations for comparison (%d)', len(elevation))
        return result

    # Change the values to arrays.
    elevation = np.array(elevation)
    position = np.array(position)

    # Create the array of ratios.
    ratios = su.create_image((length), 0.0)

    # Work out the maximum angle.
    for indx in range(len(elevation) - 1):
        # Reset the angles to zeros.
        ratios *= 0.0

        # Difference from the reference point, i.
        delta_ele = elevation[indx+1:] - elevation[indx]
        delta_len = position[indx+1:] - position[indx]
        delta_pos = position[indx]
        delta_ratio = delta_ele / delta_len

        # Get the angle between the reference and the next.
        # Does this to the end.
        for j in range(len(delta_ele)):
            ratios[j] = delta_ratio[j]

        # Find the max angle position.
        pos = int(delta_pos)
        max_ratio = np.amax(ratios)
        max_angle = math.atan(max_ratio)
        result[pos] = math.degrees(max_angle)

    return result

def process_angles(elevation, no_data):
    """Process the angles column wise."""
    (_, width) = elevation.shape
    angles = su.create_image(elevation.shape, no_data)

    for indx in range(width):
        logging.debug('Processing column: %d', indx)
        col_data = elevation[:, indx]
        angles[:, indx] = process_column(col_data.flatten(), no_data)

    return angles.copy()

def subtract_altitude(angles, altitude, no_data):
    """Subtract the altitude."""
    (height, width) = angles.shape
    for row in range(height):
        for col in range(width):
            if angles[row][col] != no_data:
                angles[row][col] = altitude - angles[row][col]

    return angles.copy()

def interpolate(x_angle, y_secs, no_data):
    """Interpolate for the zero crossing, i.e. sunset or rise."""
    zero_crossing = no_data
    if x_angle[0] <= 0.0 and x_angle[1] >= 0.0:
        zero_crossing = np.interp(0.0, x_angle, y_secs)

    return zero_crossing

def compute_sunrise(prior, now, prior_secs, now_secs, no_data, sunrise, sunset):
    """Computing the sunrise."""
    logging.info('Computing the sunrise...')
    if prior.shape == now.shape:
        (height, width) = now.shape
        for row in range(height):
            for col in range(width):
                if sunrise[row][col] == no_data and prior[row][col] != no_data and now[row][col] != no_data:
                    if prior[row][col] <= 0 and now[row][col] >= 0:
                        x_angle = [prior[row][col], now[row][col]]
                        y_secs = [prior_secs, now_secs]
                        value = interpolate(x_angle, y_secs, no_data)
                        if sunset[row][col] == no_data:
                            sunrise[row][col] = value

    return sunrise.copy()

def compute_sunset(prior, now, prior_secs, now_secs, no_data, sunset):
    """Computing the sunset."""
    logging.info('Computing the sunset...')
    if prior.shape == now.shape:
        (height, width) = now.shape
        for row in range(height):
            for col in range(width):
                if sunset[row][col] == no_data and prior[row][col] != no_data and now[row][col] != no_data:
                    if prior[row][col] >= 0 and now[row][col] <= 0:
                        x_angle = [now[row][col], prior[row][col]]
                        y_secs = [now_secs, prior_secs]
                        sunset[row][col] = interpolate(x_angle, y_secs, no_data)

    return sunset.copy()

def fill_sun_void(pad_rows, pad_cols, height, width, no_data, time, data):
    """Fill the void left with valid sun rise / set."""
    for row in range(pad_rows, pad_rows + height):
        for col in range(pad_cols, pad_cols + width):
            if data[row][col] == no_data:
                data[row][col] = time

    return data.copy()

def compute_light_in_seconds(sunrise, sunset, no_data):
    """Difference the values between sun rise and set."""
    (height, width) = sunrise.shape
    light_secs = su.create_image((height, width), no_data)
    for row in range(height):
        for col in range(width):
            if sunrise[row][col] != no_data and sunset[row][col] != no_data:
                light_secs[row][col] = sunset[row][col] - sunrise[row][col]

    return light_secs.copy()

def clean_given_surface(surface, data, no_data):
    """If the surface is a no data, so should the time."""
    if surface.shape == data.shape:
        (height, width) = surface.shape
        for row in range(height):
            for col in range(width):
                if surface[row][col] == no_data:
                    data[row][col] = no_data
    else:
        logging.error('Shape is not the same size!')

    return data.copy()

def get_percentage_light(light_in_seconds, no_data, seconds_of_light):
    """Comput the percentage of light."""
    logging.info('Computing the percentage of light...')
    (height, width) = light_in_seconds.shape
    percentage = su.create_image(light_in_seconds.shape, 0, dtype=np.int16)
    for row in range(height):
        for col in range(width):
            if light_in_seconds[row][col] != no_data:
                percentage[row][col] = int(100.0 * light_in_seconds[row][col] / seconds_of_light)

    return percentage

def preprocess_surface(surface_file, output_path, gsd):
    """Optionally resample the surface to 1.0m GSD."""
    logging.info('Surface preprocess...')
    resampled = False
    surface_tmpname = surface_file
    (srcEpsg, ground_x, ground_y, no_data) = sr.get_epsg(surface_tmpname)
    force_resample = False
    if srcEpsg != None:
        dstEpsg = 0
        if not sg.is_valid_utm_epsg(srcEpsg):
            dstEpsg = sg.get_utm_epsg_from_epsg(srcEpsg, ground_x, ground_y)
            force_resample = True
        else:
            dstEpsg = srcEpsg

        if force_resample or sr.get_gsd(surface_tmpname) < gsd:
            logging.info('Reampling %s to %f...' % (surface_file, gsd))
            temp_name = next(tempfile._get_candidate_names())
            surface_tmpname = os.path.join(output_path, temp_name + '.tif')
            sr.resample_image(surface_file, surface_tmpname, srcEpsg, dstEpsg, gsd, no_data)
            resampled = True

    return resampled, surface_tmpname

def load_surface(surface_file):
    """Load the surface."""

    logging.info('Loading (%s) ...' % (surface_file))

    # Set the failure defaults.
    padded = None
    metadata = []
    success = False

    # Get the solar image.
    dem = sr.SolarImage()

    # Open the DEM.
    if dem.open_image(surface_file):

        logging.info('Surface was opened!')

        # Get the size of the image.
        (height, width) = dem.shape()

        # Max length in the image so we can rotate freely.
        max_length = int(math.hypot(height, width) + 1)

        # Get the DEM data.
        hgt = dem.get_bands(1)

        # Get the padding to place the DEM in the center.
        pad_cols = int((max_length - width) / 2.0)
        pad_rows = int((max_length - height) / 2.0)

        # Place the dem in the center.
        padded = sr.padded_image(hgt, pad_rows, pad_cols)

        # Compute the latitude and longitude of the center.
        # This is ultimately what we are going to rotate about.
        (e, n) = dem.get_centroid_ground()

        logging.info('Centroid (E: %.3f, N: %.3f)' % (e, n))

        # Convert the Eastings and Northings into Latitude and Longitude.
        epsg_code = dem.get_epsg_code()
        (lat, lon) = sg.get_lat_lon(epsg_code, e, n)

        logging.info('Centroid %d (Lat: %.8f, Lon: %.8f)' % (epsg_code, lat, lon))

        # Get the average GSD.
        gsd = dem.get_avg_gsd()

        # Get the no data value.
        no_data = dem.no_data()

        # Set the no data value to -9999
        if no_data is None:
            no_data = -9999

        # Set the metadata.
        metadata = [pad_rows, pad_cols, height, width, lat, lon, gsd, no_data, dem.profile(), dem.get_affine()]

        # Everything worked.
        success = True
    else:
        logging.error('Could not open the DEM (%s).' % (surface_file))

    return success, padded, metadata

def get_colormap(output_path, base, title, sunrise_time, sunset_time, percentage_light, affine, color_scheme):
    """Write colormap."""
    name = os.path.join(output_path, base + '_light_perc.png')
    logging.info('Saving color map data (%s)' % (name))

    sr_ss_text = 'sunrise: %02d:%02d:%02d sunset: %02d:%02d:%02d' % (sunrise_time.hour, sunrise_time.minute, sunrise_time.second, sunset_time.hour, sunset_time.minute, sunset_time.second)

    (height, width) = percentage_light.shape
    width_inches = 10.0
    height_inches = width_inches * float(height) / float(width)

    fig = plt.figure()
    fig.set_size_inches(width_inches + 1, height_inches)
    ax = plt.subplot(111)
    im = ax.imshow(percentage_light, cmap = color_scheme)
    plt.title(title)
    fig.suptitle('Percentage of daylight', fontsize=12)
    plt.xlabel(sr_ss_text)
    fig.colorbar(im, orientation='vertical')
    fig.savefig(name)

    # Write pngw.
    name = os.path.join(output_path, base + '_light_perc.pngw')
    sr.write_affine(name, affine)

def get_radiation_product(sunrise, sunset, sunrise_time, sunset_time, local_date, time_zone, lat, lon, no_data):
    """Get the radiation product."""
    (x_sec, y_rad) = precompute_radiation(sunrise_time, sunset_time, local_date, time_zone, lat, lon)

    # Iterate across the image.
    success = False
    radiation = None
    if sunrise.shape == sunset.shape: 
        (height, width) = sunrise.shape
        radiation = su.create_image((height, width), no_data)
        for row in range(height):
            for col in range(width):
                sunrise_secs = sunrise[row][col]
                sunset_secs = sunset[row][col]
                if sunrise_secs != no_data and sunset_secs != no_data:
                    radiation[row][col] = get_radiation(sunrise_secs, sunset_secs, x_sec, y_rad) 
        success = True      
        # name = os.path.join(output_path, base + '_radiation.tif')
        # logging.info('Saving radiation data (%s)' % (name))
        # io.imsave(name, radiation)
        
    else:
        logging.error('Sunrise and sunset shape are different!')
    
    return success, radiation

def precompute_radiation(sunrise_time, sunset_time, local_date, time_zone, lat, lon):
    """Precompute the radiation."""
    logging.info('Precomputing the radiation...')
    sunrise_secs = su.get_seconds_from_datetime(sunrise_time)
    sunset_secs = su.get_seconds_from_datetime(sunset_time)
    increment = 600
    sunrise_secs = int((sunrise_secs / increment) + 1) * increment
    sunset_secs = int((sunset_secs / increment) - 1) * increment

    x_sec = []
    y_rad = []
    for secs in range(sunrise_secs, sunset_secs, 60):
        (hr, min, sec) = su.get_time_from_seconds(secs)
        d = su.combine_datetime(local_date, hr, min, sec, time_zone)
        alt_deg = get_altitude(lat, lon, d)
        rad = radiation.get_radiation_direct(d, alt_deg)
        if rad >= 0 and rad < 1500:
            x_sec.append(secs)
            y_rad.append(rad)

    return x_sec, y_rad

def get_radiation(sunrise_secs, sunset_secs, x_sec, y_rad):
    """Get the solar radiation given the sunrise and sunset in seconds."""
    x_sec_local = []
    y_rad_local = []

    # Get the section of the radiation array.
    area = 0
    for indx in range(len(x_sec)):
        if x_sec[indx] >= sunrise_secs and sunset_secs >= x_sec[indx]:
            x_sec_local.append(x_sec[indx])
            y_rad_local.append(y_rad[indx])
    
    # If we have enough points compute the area.
    if len(x_sec_local) >= 2:
        area = np.trapz(y_rad_local, x_sec_local) / 3600

    # Return what we have, zero is an error.
    return area

def process_time(time, local_date, time_zone, lat, lon, surface, no_data):
    logging.info('Process time %d' % (time))
    (h, m, s) = su.get_time_from_seconds(time)
    logging.info('Time: %.3f (%02d:%02d:%7.5f)', time, h, m, s)

    # Combine the date and time.
    local_datetime = su.combine_datetime(local_date, h, m, int(s), time_zone)

    # Get the Sun azimuth for the time.
    sun_azimuth = get_azimuth(lat, lon, local_datetime)
    logging.info('Sun azimuth: %.5f', sun_azimuth)

    # Rotate the DEM to make the sun be at the bottom.
    rotation_angle = sun_azimuth
    rotated_surface = sr.rotate_image(surface, rotation_angle)

    # Work out the max angle from a point to the surface.
    angles = process_angles(rotated_surface, no_data)

    # Get the sun altitude.
    sun_altitude = get_altitude(lat, lon, local_datetime)
    logging.info('Sun altitude: %.5f', sun_altitude)

    # Work out the angle difference from the sun., no_data
    # Negative values imply the point is in the shadow.
    delta = subtract_altitude(angles, sun_altitude, no_data)

    # Rotate back the angle.
    rotated_delta = sr.rotate_image(delta, -rotation_angle)
 
    logging.info('Adding to the queue')
    tmp = [time, rotated_delta.copy()]
    return tmp

def process_surface(surface, metadata, local_date, sunrise_time, sunset_time, radiation, tiff, cmap, workers):
    """Process the surface data."""
    logging.info('Processing surface...')

    # Some metadata.
    pad_rows = metadata[0]
    pad_cols = metadata[1]
    height = metadata[2]
    width = metadata[3]
    lat = metadata[4]
    lon = metadata[5]
    no_data = metadata[7]
    profile = metadata[8]
    affine = metadata[9]
    time_zone = metadata[10]
    increments = metadata[11]
    output_path = metadata[12]
    surface_filename = metadata[13]

    # Get the time array.
    times = su.get_processing_times(sunrise_time, sunset_time, increments)

    # For every time.
    with tqdm(total=len(times), desc="Processing time") as bar1:
        pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
        futures = []
        for time in times:
            futures.append(pool.submit(process_time, time, local_date, time_zone, lat, lon, surface, no_data))
 
        for x in concurrent.futures.as_completed(futures):
            q.put(x.result())
            bar1.update(1)

    first = True
    previous_delta = None
    previous_time = None
    sunrise = None
    sunset = None
    while not q.empty():
        tmp = q.get()

        if not first:
            logging.info('Processing times! %d to %d' % (previous_time, tmp[0]))
            sunrise = compute_sunrise(previous_delta, tmp[1], previous_time, tmp[0], no_data, sunrise, sunset)
            sunset = compute_sunset(previous_delta, tmp[1], previous_time, tmp[0], no_data, sunset)
        else:
            logging.info('Reference ' + str(tmp[0]))
            sunset = su.create_image(tmp[1].shape, no_data)
            sunrise = su.create_image(tmp[1].shape, no_data)

        # Copy the delta to the previous.
        first = False
        previous_delta = tmp[1].copy()
        previous_time = tmp[0]
        bar1.update(1)

    with tqdm(total=7, desc="Creating output") as bar:
        logging.info('Creating the output...')

        # Fill the voids and clip the padding.
        end_time = len(times) - 1
        sunrise = fill_sun_void(pad_rows, pad_cols, height, width, no_data, times[0], sunrise)
        sunrise = sr.clip_padded_image(sunrise, pad_rows, pad_cols, no_data)
        sunset = fill_sun_void(pad_rows, pad_cols, height, width, no_data, times[end_time], sunset)
        sunset = sr.clip_padded_image(sunset, pad_rows, pad_cols, no_data)
        surface = sr.clip_padded_image(surface, pad_rows, pad_cols, no_data)
        bar.update(1)

        # Get the light in seconds per point.
        light_in_seconds = compute_light_in_seconds(sunrise, sunset, no_data)
        bar.update(1)
        
        # Clean the data up, i.e. no surface point no output.
        sunset = clean_given_surface(surface, sunset, no_data)
        sunrise = clean_given_surface(surface, sunrise, no_data)
        light_in_seconds = clean_given_surface(surface, light_in_seconds, no_data)
        bar.update(1)

        # Write the outputs.
        (_, tail) = os.path.split(surface_filename)
        (base, _) = os.path.splitext(tail)
        base += '_' + local_date.isoformat()
        if tiff:
            name = os.path.join(output_path, base + '_sunset.tif')
            logging.info('Saving sunset data (%s)' % (name))
            sr.write_output(name, sunset, profile)
            name = os.path.join(output_path, base + '_sunrise.tif')
            logging.info('Saving sunrise data (%s)' % (name))
            sr.write_output(name, sunrise, profile)
            name = os.path.join(output_path, base + '_light_secs.tif')
            logging.info('Saving light data (%s)' % (name))
            sr.write_output(name, light_in_seconds, profile)
        bar.update(1)

        # Get the percentage of light.
        seconds_of_light = times[end_time] - times[0]
        percentage_light = get_percentage_light(light_in_seconds, no_data, seconds_of_light)
        if tiff:
            name = os.path.join(output_path, base + '_light_perc.tif')
            logging.info('Saving percentage light data (%s)' % (name))
            sr.write_output(name, percentage_light, profile, dn_type=np.int16)
        bar.update(1)

        # Colored image.
        get_colormap(output_path, base, local_date.isoformat(), sunrise_time, sunset_time, percentage_light, affine, cmap)
        bar.update(1)

        # Radiation.
        if radiation:
            (success, radiation_data) = get_radiation_product(sunrise, sunset,     sunrise_time, sunset_time, local_date, time_zone, lat, lon, no_data)
            if success:
                name = os.path.join(output_path, base + '_radiation.tif')
                logging.info('Saving radiation data (%s)' % (name))
                sr.write_output(name, radiation_data, profile)
                
        bar.update(1)

        logging.info('The end...')

    return light_in_seconds
