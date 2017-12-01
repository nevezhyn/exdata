#! /bin/bash

sudo docker run -d --name=influxdb --net=influxdb -v $(pwd)/configs/influxdb.conf:/etc/influxdb/influxdb.conf:ro -v $(pwd)/data/influx:/var/lib/influxdb influxdb -config /etc/influxdb/influxdb.conf &
sleep 5
sudo docker run -d --name=telegraf --net=container:influxdb -v $(pwd)/configs/telegraf.conf:/etc/telegraf/telegraf.conf:ro telegraf &
sleep 5
sudo docker run -d -p 9092:9092 --name=kapacitor -h kapacitor --net=influxdb -v $(pwd)/configs/kapacitor.conf:/etc/kapacitor/kapacitor.conf:ro -v $(pwd)/data/kapacitor:/var/lib/kapacitor -e KAPACITOR_INFLUXDB_0_URLS_0=http://influxdb:8086 kapacitor &
sleep 5
sudo docker run -d --name=chronograf -p 8888:8888 --net=influxdb chronograf --influxdb-url=http://influxdb:8086 &
sleep 5
sudo docker run -d --name=exdata -h exdata -p 8181:8181 --net=influxdb exdata &
