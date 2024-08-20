#!/bin/bash

# docker login ghcr.io -u szachovy
docker service create \
  --with-registry-auth \
  --detach \
  --name superset \
  --secret superset_secret_key \
  --publish 8088:8088 \
  --constraint 'node.role!=manager' \
  --constraint 'node.labels.preferred==true' \
  --env VIRTUAL_IP_ADDRESS="${1}" \
  ghcr.io/szachovy/superset-cluster:latest

# PLACEMENT PREF DOES NOT WORK, FIND ALTERNATIVE

# docker service create \
#   --with-registry-auth \
#   --detach \
#   --name superset \
#   --secret superset_secret_key \
#   --publish 8088:8088 \
#   --constraint 'node.role!=manager' \
#   --env VIRTUAL_IP_ADDRESS="10.145.211.155" \
#   --placement-pref 'spread=node.labels.preferred' \
#   --health-cmd="ip addr show | grep 10.145.211.155" \
#   --health-start-period=1s \
#   --health-interval=10s \
#   --health-retries=3 \
#   --health-timeout=5s \
#   --restart-condition any \
#   --restart-delay 10s \
#   --restart-max-attempts 1 \
#   ghcr.io/szachovy/superset-cluster:latest

# docker node update --label-add preferred=true wiktor-min-sles
  # --network superset-network \
# docker run \
#   --detach \
#   --name redis \
#   --network superset-network \
#   --hostname redis \
#   redis

# docker service create \
#   --detach \
#   --name redis \
#   --hostname redis \
#   --network superset-network \
#   --publish 6379:6379 \
#   redis
# --publish published=6379,target=6379 \
# docker build \
#   --tag superset \
#   $(pwd)/services/superset

# echo $(openssl rand -base64 42) >> $(pwd)/services/superset/superset_secret_key

# docker run \
#   --detach \
#   --name superset \
#   --volume $(pwd)/services/superset/superset_secret_key:/run/secrets/superset_secret_key \
#   --network superset-network \
#   --publish 8088:8088 \
#   --env VIRTUAL_IP_ADDRESS="${1}" \
#   superset
  # ghcr.io/szachovy/superset-cluster:latest
