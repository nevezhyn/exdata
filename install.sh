#! /bin/bash
sudo apt install docker.io -yq
sudo docker network create influxdb
sudo docker pull influxdb
sudo docker pull telegraf
sudo docker pull kapacitor
sudo docker pull chronograf
sudo docker build . -t exdata