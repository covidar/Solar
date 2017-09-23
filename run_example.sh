#!/bin/sh

# Run a small patch producing extra TIFF file outputs.
python3 ./src/solar.py -s ./tests/data/Patch_DEM.tif -o ./tests/results/ -y 2016 -m 9 -d 14 -w 3 -i 5 -f
