#!/bin/bash

MYSQL_ROOT_PASSWORD=mysql

docker build \
  --build-arg SERVER_ID=$((RANDOM % 4294967295 + 1)) \
  --build-arg MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
  --build-arg MYSQL_DATABASE=superset \
  --tag mysql-server \
  /opt/superset-cluster/mysql-server

docker run \
  --detach \
  --restart always \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --network host \
  mysql-server
