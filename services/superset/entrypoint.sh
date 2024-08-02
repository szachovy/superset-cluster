#!/bin/bash

superset fab create-admin \
  --username "superset" \
  --firstname "superset" \
  --lastname "superset" \
  --email "superset@cluster.com" \
  --password "cluster"

superset db upgrade
superset init

INITIAL_MYSQL_CONNECTION_STRING="mysql+mysqlconnector://superset:cluster@${VIRTUAL_IP_ADDRESS}:6446/superset"

# if superset test_db "${INITIAL_MYSQL_CONNECTION_STRING}" --connect-args {}; then
#   superset set-database-uri \
#     --database_name \
#       "MySQL" \
#     --uri \
#       "${INITIAL_MYSQL_CONNECTION_STRING}"
# fi

celery \
  --app superset.tasks.celery_app:app worker \
  --pool prefork \
  --concurrency 4 \
  -O fair \
  --detach

/usr/bin/run-server.sh &

if superset test_db "${INITIAL_MYSQL_CONNECTION_STRING}" --connect-args {}; then
  /app/set-database-uri.exp
fi

tail -f /dev/null
