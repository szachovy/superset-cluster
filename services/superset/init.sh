#!/bin/bash

# docker build \
#   --build-arg VIRTUAL_IP_ADDRESS="172.18.0.8" \
#   --build-arg ENVIRONMENT="testing" \
#   --tag superset \
#   /opt/superset-cluster/services/superset

docker build \
  --tag superset \
  /opt/superset-cluster/services/superset

docker build \
  --tag superset-cluster-service:latest \
  ./services/superset 

# docker build \
#   --build-arg VIRTUAL_IP_ADDRESS="${1}" \
#   --build-arg ENVIRONMENT="${2}" \
#   --tag superset \
#   $(pwd)/services/superset

docker login ghcr.io -u szachovy

docker service create \
  --with-registry-auth \
  --detach \
  --name superset \
  --secret superset_secret_key \
  --network superset-network \
  --publish 8088:8088 \
  --env VIRTUAL_IP_ADDRESS="172.18.0.8" \
  --health-start-period "300s" \
  ghcr.io/szachovy/superset-cluster:latest

nano /opt/superset-cluster/services/superset/superset_secret_key

docker run \
  --detach \
  --name superset \
  --volume /opt/superset-cluster/services/superset/superset_secret_key:/run/secrets/superset_secret_key \
  --network superset-network \
  --publish 8088:8088 \
  --env VIRTUAL_IP_ADDRESS="172.18.0.8" \
  superset
  #ghcr.io/szachovy/superset-cluster:latest

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

docker service scale superset=1