#!/usr/bin/env python3

"""Solar main program."""

import argparse
from datetime import date
import logging
import os
import sys
import warnings

# Solar defined code.
import solar_utility as su
import solar_angle_processor as sa

logging.basicConfig(filename='./logs/solar.log',
                    format ='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                    datefmt = "%Y-%m-%d %H:%M:%S", filemode='w', level=logging.INFO)

# Don't warn for Future stuff.
warnings.simplefilter(action='ignore', category=FutureWarning)

def arg_parse():
    """Parse the arguments."""
    parser = argparse.ArgumentParser(description="Solar analysis from a surface.")
    parser.add_argument('-s', '--surface', type=str, required=True)
    parser.add_argument('-o', '--output_path', type=str, required=True)
    parser.add_argument('-y', '--year', type=int, required=True)
    parser.add_argument('-m', '--month', type=int, required=True)
    parser.add_argument('-d', '--day', type=int, required=True)
    parser.add_argument('-n', '--no_data', type=float, default=-9999)
    parser.add_argument('-t', '--time_zone', type=str, default='US/Pacific')
    parser.add_argument('-i', '--increments', type=int, default=1)
    parser.add_argument('-g', '--gsd', type=float, default=1.0)
    parser.add_argument('-r', '--radiation', dest='radiation', action='store_true')
    parser.add_argument('-f', '--tiff', dest='tiff', action='store_true')
    parser.add_argument('-w', '--workers', type=int, default=4)
    parser.set_defaults(radiation=False)
    parser.set_defaults(tiff=False)
    args = parser.parse_args()
    logging.info(args)
    return args

def main():
    """Main function."""
    logging.info('Starting...')

    # Parse the arguments.
    args = arg_parse()

    print('Processing surface: ', args.surface)

    # Get the surface's GSD.
    (resampled, surface_filename) = sa.preprocess_surface(args.surface, args.output_path, args.gsd)

    # Open the surface.
    (success, surface, metadata) = sa.load_surface(surface_filename)

    # Exit if the surface could not be loaded.
    if not success:
        sys.exit(1)

    # Get the sunrise and sunset.
    lat = metadata[4]
    lon = metadata[5]
    (sunrise, sunset) = su.get_sun_rise_set(args.year, args.month, args.day, args.time_zone,
                                            lat, lon)
    # Get the date.
    local_date = date(args.year, args.month, args.day)

    print('Processing date: ', local_date.isoformat())

    # Append to the metadata.
    metadata.append(args.time_zone)
    metadata.append(args.increments)
    metadata.append(args.output_path)
    metadata.append(args.surface)

    # Process the surface.
    sa.process_surface(surface, metadata, local_date, sunrise, sunset, args.radiation, args.tiff,
                       args.workers)

    # Clean up the temporary file.
    if resampled:
        if os.path.exists(surface_filename):
            logging.info('Deleting (%s)' % (surface_filename))
            os.remove(surface_filename)

    logging.info('Terminated...')
    print('Done!')

if __name__ == '__main__':
    main()
