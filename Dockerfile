# Use an official Python runtime as a parent image
FROM python:3.5-slim
FROM ubuntu:16.04

# Set the working directory to /app
WORKDIR /solar

# Copy the current directory contents into the container at /app
COPY . /solar

RUN apt-get update && apt-get install -y \
        software-properties-common \
        python-software-properties

RUN add-apt-repository -y ppa:ubuntugis/ppa

COPY ./requirements.txt .

RUN apt-get install -y \
        python3 \
        python3-pip \
        python3-tk \
        gdal-bin \
        python3-gdal \
        libgdal-dev && \
        pip3 install --upgrade pip && \
        pip3 install -r requirements.txt

RUN rm requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

#ENV DISPLAY :0
