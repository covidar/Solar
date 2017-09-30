# Solar
This is an application that takes DEM's, typically made from drone data, and uses the movement of the Sun to predict the percentage of daylight. This obviously has applications in Solar panel analysis and agriculture.

# Techonolgy
## Idea
Given that we have been given the opportunity to create our own maps and indeed surface models through drones it made sense to enable solar analysis of the data. Other web based products are based on old data, sometimes many years out of date, and this allows the computation hours after collection.

## Process flow
* Resample the surface model to a higher resolution.
* Given the date and the location workout the Sun azimuth.
* Rotate the terrain so that the sun is at the bottom.
* With the Sun altitude work out if the sun would be blocked by the adjacent pixel.
* Compute the effective sunrise and sunset for each pixel in the surface.
* Present the results.

## Limitations
* If a pixel is impinged it is considered to be black.
* The process space is the DEM itself and of course any pixel could be impinged by a huge mountain next to the processed surface.
* The effective sunrise and sunset for each pixel is an approximation given the number of time increments chosen for the computation. More accurate values require longer processing time.
* The radiation product is based on a clear sky model, i.e. a perfect day!

# Dependencies
This code has a number of dependencies with varying degrees of complexity for installation. However, choices have been made to make this process simple.

* [futures](https://pypi.python.org/pypi/futures)
* [matplotlib](https://matplotlib.org/)
* [osgeo](https://pypi.python.org/pypi/GDAL)
* [nose](http://nose.readthedocs.io/en/latest/)
* [pysolar](https://pypi.python.org/pypi/Pysolar)
* [pytz](https://pypi.python.org/pypi/pytz)
* [rasterio](https://github.com/mapbox/rasterio)
* [skimage](http://scikit-image.org/)
* [tqdm](https://pypi.python.org/pypi/tqdm)
* [utm](https://pypi.python.org/pypi/utm)

# Docker
TBD

# Running a job
## Commandline options
usage: solar.py [-h] -s SURFACE -o OUTPUT_PATH -y YEAR -m MONTH -d DAY
                [-n NO_DATA] [-t TIME_ZONE] [-i INCREMENTS] [-g GSD] [-r] [-f]
                [-w WORKERS] [-c CMAP]
solar.py: error: the following arguments are required: -s/--surface, -o/--output_path, -y/--year, -m/--month, -d/--day

-s - DEM in the form of a TIFF with appopriate georeferencing
-o - Output path for the results
-y - Year to process for the sun
-m - Month to process
-d - Day to process
-n - DEM no data value override, otherwise read from the surface
-t - Time zone of the surface
-i - Number of increments to process, default is 3 namely sunrise, noon and sunset
-g - GSD in meters. A good value is 0.5m
-r - Compute the radiation
-f - Write the output files in TIFF form
-w - Number of threads to use, ideally the number of increments
-c - CMAP from [Matplotlib](https://matplotlib.org/users/colormaps.html) for coloring the output

## Example
python3 ./src/solar.py -s ./tests/data/Patch_DEM.tif -o ./tests/results/ -y 2016 -m 9 -d 14 -w 3 -i 5 -f

This is also runnable by using the run_example.sh script in the root folder.

## Results

![Percent Light](/examples/Patch_DEM_2016-09-14_light_perc.png)

In this example it shows a small area of a hillside with some trees. The area with a lower percentage is covered with trees.

# Tests
These are under developement and will evolve into validating the science when ground truth is available. These will likely steer the develeopment work.

nosetests --with-cov --cov-report html  tests/

This is also runnable by using the run_tests.sh script in the root folder.

# Acknowledgements
The help and inspiration of Autonomous Imagery.

# Feedback

Add feedback should be sent to solar@timelymaps.com
