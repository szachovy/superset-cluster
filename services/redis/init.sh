#!/bin/bash

docker build \
  --tag redis \
  $(pwd)/services/redis

docker run \
  --detach \
  --name redis \
  --hostname redis \
  --network superset-network \
  redis
