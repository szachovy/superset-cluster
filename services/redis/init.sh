#!/bin/bash

docker build \
  --tag redis \
  $(pwd)/services/redis

docker run \
  --detach \
  --name redis \
  --network superset-network \
  --hostname redis \
  redis
