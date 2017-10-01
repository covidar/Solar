#!/bin/sh

# list
#docker ps -a

# clean
#docker system prune -a

# build
docker build -t solar .

# tag the repo
#docker tag solar:latest timelymaps/solar:latest

# login before the push
#docker login

# push it
#docker push timelymaps/solar:latest