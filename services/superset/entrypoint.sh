#!/bin/bash

set -euo pipefail

DB_PASSWORD=$(< /run/secrets/mysql_superset_password)
DB_URI="mysql+mysqlconnector://superset:${DB_PASSWORD}@${VIRTUAL_IP_ADDRESS}:6446/superset"

if superset test_db "$DB_URI" --connect-args {} 2>&1 \
    | DB_PASSWORD="$DB_PASSWORD" python3 /app/redact_secret.py; then
  set -x

  superset fab create-admin \
  --username "superset" \
  --firstname "superset" \
  --lastname "superset" \
  --email "superset@cluster.com" \
  --password "$(< /run/secrets/superset_admin_password)"

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
