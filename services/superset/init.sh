#!/bin/bash

docker build \
  --tag superset \
  $(pwd)/services/superset

docker run \
  --detach \
  --name superset \
  --publish 8088:8088 \
  --network superset-network \
  superset

sleep 25
docker exec superset superset fab create-admin --username admin --firstname admin --lastname admin --email admin@admin.com --password admin
docker exec superset superset db upgrade
docker exec superset superset load_examples
docker exec superset superset init
nohup docker exec superset celery --app=superset.tasks.celery_app:app worker --pool=prefork -O fair -c 4 > /dev/null 2>&1 &
