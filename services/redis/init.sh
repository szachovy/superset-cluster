#!/bin/bash

docker build \
  --tag redis \
  /opt/redis

docker run \
  --detach \
  --restart always \
  --name redis \
  --hostname redis \
  --network superset-network \
  redis
