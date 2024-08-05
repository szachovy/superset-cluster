#!/bin/bash

# docker login ghcr.io -u szachovy
# docker service create \
#   --with-registry-auth \
#   --detach \
#   --name superset \
#   --secret superset_secret_key \
#   --network superset-network \
#   --publish 8088:8088 \
#   --env VIRTUAL_IP_ADDRESS="172.18.0.8" \
#   --health-start-period "300s" \
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
  --env VIRTUAL_IP_ADDRESS="${1}" \
  --health-start-period "${2}" \
  superset
  #ghcr.io/szachovy/superset-cluster:latest

# docker run \
#   --detach \
#   --name superset \
#   --volume $(pwd)/services/superset/superset_secret_key:/run/secrets/superset_secret_key \
#   --network superset-network \
#   --publish 8088:8088 \
#   --env VIRTUAL_IP_ADDRESS="172.18.0.8" \
#   superset

# docker service create \
#   --detach \
#   --name superset \
#   --secret superset_secret_key \
#   --network superset-network \
#   --publish 8088:8088 \
#   --env VIRTUAL_IP_ADDRESS="${1}" \
#   --env ENVIRONMENT="${2}" \
#   superset

# docker run \
#   --detach \
#   --name superset \
#   --network superset-network \
#   --publish 8088:8088 \
#   superset

# export VIRTUAL_IP_ADDRESS="172.18.0.8"
# export ENVIRONMENT="prod"

# docker compose \
#   --file /opt/superset-cluster/services/superset/docker-compose.yml up initcontainer \
# && \
# docker compose \
#   --file /opt/superset-cluster/services/superset/docker-compose.yml up maincontainer \
#   --detach

# docker compose \
#   --file /opt/superset-cluster/services/superset/docker-compose.yml down maincontainer

# docker compose \
#   --file /opt/superset-cluster/services/superset/docker-compose.yml down initcontainer

# docker service scale superset=1
