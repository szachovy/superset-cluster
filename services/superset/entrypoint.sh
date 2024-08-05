#!/bin/bash

superset fab create-admin \
  --username "superset" \
  --firstname "superset" \
  --lastname "superset" \
  --email "superset@cluster.com" \
  --password "cluster"

superset db upgrade
superset init

/usr/bin/run-server.sh &

if superset test_db \
    "mysql+mysqlconnector://superset:cluster@${VIRTUAL_IP_ADDRESS}:6446/superset" \
    --connect-args {}; then
  /app/set-database-uri.exp
fi

celery \
  --app superset.tasks.celery_app:app worker \
  --pool prefork \
  --concurrency 4 \
  -O fair
