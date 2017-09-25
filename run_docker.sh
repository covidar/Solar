#!/bin/sh

mkdir results

sudo docker run -v /media/neil/PATRIOT/Dev/Python/Solar/Solar/results:/results solar python3 src/solar.py -s tests/data/Patch_DEM.tif -o /results -y 2016 -m 12 -d 12