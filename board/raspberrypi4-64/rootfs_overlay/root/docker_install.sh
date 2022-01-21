#!/bin/bash

wget --no-check-certificate https://download.docker.com/linux/static/stable/aarch64/docker-20.10.9.tgz
tar xzvf docker-20.10.9.tgz 
cp  docker/* /usr/bin
dockerd &
