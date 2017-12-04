#! /bin/bash
CONTAINER_ID=$(sudo docker ps -a -q -f name=exdata)
IMAGE_ID=$(sudo docker images -q exdata)
sudo docker stop $CONTAINER_ID
sudo docker rm $CONTAINER_ID
sudo docker rmi $IMAGE_ID
sudo docker build . -t exdata