#!/bin/bash

set -euxo pipefail

if superset test_db \
    "mysql+mysqlconnector://superset:$(< /run/secrets/mysql_superset_password)@${VIRTUAL_IP_ADDRESS}:6446/superset" \
    --connect-args {}; then
  
  superset fab create-admin \
  --username "superset" \
  --firstname "superset" \
  --lastname "superset" \
  --email "superset@cluster.com" \
  --password "cluster"

  superset db upgrade
  superset init
  
  /app/set_database_uri.exp
  /usr/bin/run-server.sh &

  celery \
    --app superset.tasks.celery_app:app worker \
    --pool prefork \
    --concurrency 4 \
    -O fair &
  
  wait
else
  echo "Could not connect to the MySQL database"
  exit 1
fi
