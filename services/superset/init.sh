#!/bin/bash

VIRTUAL_IP_ADDRESS="${1}"
PRELOAD_EXAMPLES="${2}"

docker build \
  --build-arg PRELOAD_EXAMPLES="${PRELOAD_EXAMPLES}" \
  --tag superset \
  $(pwd)/services/superset

docker run \
  --detach \
  --name superset \
  --network superset-network \
  --publish 8088:8088 \
  --env "VIRTUAL_IP_ADDRESS=${VIRTUAL_IP_ADDRESS}" \
  superset
