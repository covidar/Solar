#!/bin/sh

# Run a small patch producing extra TIFF file outputs.
python3 ./src/solar.py -s ./tests/data/Patch_DEM.tif -o ./examples/ -y 2016 -m 9 -d 14 -w 3 -i 5 -f
