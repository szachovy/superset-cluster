#!/bin/bash

docker build \
  --build-arg SERVER_ID=$((RANDOM % 4294967295 + 1)) \
  --tag mysql-server \
  /opt/superset-cluster/mysql-server

docker run \
  --detach \
  --restart always \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --network host \
  mysql-server
