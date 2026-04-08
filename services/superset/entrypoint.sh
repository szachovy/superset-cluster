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
  gunicorn \
    --bind 0.0.0.0:8088 \
    --workers 4 \
    --worker-class gevent \
    --timeout 120 \
    --limit-request-line 8190 \
    --forwarded-allow-ips "*" \
    "superset.app:create_app()" &

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
