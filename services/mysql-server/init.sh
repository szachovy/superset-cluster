#!/bin/bash

MYSQL_ROOT_PASSWORD=mysql

docker build \
  --build-arg SERVER_ID=$((RANDOM % 4294967295 + 1)) \
  --build-arg MYSQL_DATABASE=superset \
  --build-arg MYSQL_USER=myuser \
  --build-arg MYSQL_PASSWORD=mypass \
  --tag mysql-server . \
  /opt/superset-cluster/mysql-server

docker run \
  --detach \
  --restart always \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --network host \
  mysql-server
#  --user myuser \
# -e MYSQL_ROOT_PASSWORD_FILE=/root/superset-mysql-root-password \