#!/bin/bash

MYSQL_IP="${1}"
PRELOAD_EXAMPLES="${2}"

docker build \
  --tag superset \
  $(pwd)/services/superset

docker run \
  --detach \
  --name superset \
  --network superset-network \
  --publish 8088:8088 \
  --env "MYSQL_IP=${MYSQL_IP}" \
  superset

sleep 25
docker exec superset superset fab create-admin --username admin --firstname admin --lastname admin --email admin@admin.com --password admin
docker exec superset superset db upgrade
if ${PRELOAD_EXAMPLES} ; then
  docker exec superset superset load_examples
fi
docker exec superset superset init
sleep 15
nohup docker exec superset celery --app=superset.tasks.celery_app:app worker --pool=prefork -O fair -c 4 > /dev/null 2>&1 &
