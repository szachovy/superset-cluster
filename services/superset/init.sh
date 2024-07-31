#!/bin/bash

docker build \
  --build-arg VIRTUAL_IP_ADDRESS="172.18.0.8" \
  --build-arg ENVIRONMENT="testing" \
  --tag superset \
  /opt/superset-cluster/services/superset

# docker build \
#   --build-arg VIRTUAL_IP_ADDRESS="${1}" \
#   --build-arg ENVIRONMENT="${2}" \
#   --tag superset \
#   $(pwd)/services/superset

docker run \
  --detach \
  --name tsuperset \
  --network superset-network \
  --publish 8088:8088 \
  test

export VIRTUAL_IP_ADDRESS="172.18.0.8"
export ENVIRONMENT="testing"

docker compose \
  --file /opt/superset-cluster/services/superset/docker-compose.yml up initcontainer \
&& \
docker compose \
  --file /opt/superset-cluster/services/superset/docker-compose.yml up maincontainer \
  --detach
