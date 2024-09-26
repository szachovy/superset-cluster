#!/bin/bash

docker service create \
  --with-registry-auth \
  --detach \
  --name superset \
  --secret superset_secret_key \
  --publish 8088:8088 \
  --network superset-network \
  --replicas 1 \
  --health-start-period=60s \
  --health-interval=30s \
  --health-retries=10 \
  --health-timeout=5s \
  --env VIRTUAL_IP_ADDRESS="${1}" \
  ghcr.io/szachovy/superset-cluster:latest
