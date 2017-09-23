#!/bin/sh

# run the tests with output to a HTML file.
nosetests --with-cov --cov-report html  tests/
