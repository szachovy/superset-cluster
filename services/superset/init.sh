#!/bin/bash

# docker login ghcr.io -u szachovy
# docker service create \
#   --with-registry-auth \
#   --detach \
#   --name superset \
#   --secret superset_secret_key \
#   --network superset-network \
#   --publish 8088:8088 \
#   --env VIRTUAL_IP_ADDRESS="${1}" \
#   ghcr.io/szachovy/superset-cluster:latest

docker build \
  --tag superset \
  $(pwd)/services/superset

echo 'vbuywuytwvty2434rggvwrvtr123' >> $(pwd)/services/superset/superset_secret_key

docker run \
  --detach \
  --name superset \
  --volume $(pwd)/services/superset/superset_secret_key:/run/secrets/superset_secret_key \
  --network superset-network \
  --publish 8088:8088 \
  --env VIRTUAL_IP_ADDRESS="172.18.0.8" \
  superset
  # ghcr.io/szachovy/superset-cluster:latest
