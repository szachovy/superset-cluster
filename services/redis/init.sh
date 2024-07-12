#!/bin/bash

docker build \
  --tag redis \
  $(pwd)/services/redis

docker run \
  --detach \
  --name redis \
  --hostname redis \
  redis

#   --network superset-network \
