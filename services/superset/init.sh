#!/bin/bash

# docker build \
#   --build-arg VIRTUAL_IP_ADDRESS="172.18.0.8" \
#   --build-arg ENVIRONMENT="testing" \
#   --tag superset \
#   $(pwd)/services/superset

docker build \
  --build-arg VIRTUAL_IP_ADDRESS="${1}" \
  --build-arg ENVIRONMENT="${2}" \
  --tag superset \
  $(pwd)/services/superset

docker run \
  --detach \
  --name superset \
  --network superset-network \
  --publish 8088:8088 \
  superset
