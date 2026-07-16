#!/bin/bash

set -euo pipefail

DB_PASSWORD=$(< /run/secrets/mysql_superset_password)
DB_URI="mysql+mysqlconnector://superset:${DB_PASSWORD}@${VIRTUAL_IP_ADDRESS}:6446/superset"

# -x stays off here: tracing this line, or superset test_db's own "SQLAlchemy
# URI" printout, would put the plaintext DB password into docker logs/docker
# service logs. Redact stdout+stderr as a backstop in case anything
# downstream still echoes the URI.
if superset test_db "$DB_URI" --connect-args {} 2>&1 \
    | DB_PASSWORD="$DB_PASSWORD" python3 -c '
import os, sys
pw = os.environ["DB_PASSWORD"]
for line in sys.stdin:
    sys.stdout.write(line.replace(pw, "<redacted>"))
    sys.stdout.flush()
'; then
  set -x

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
