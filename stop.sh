#! /bin/bash

sudo docker stop $(sudo docker ps -a -q)
sleep 5
sudo docker rm $(sudo docker ps -a -q)
