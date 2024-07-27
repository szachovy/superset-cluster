#!/bin/bash

HEALTHCHECK_START_PERIOD=20
HEALTHCHECK_INTERVAL=5
HEALTHCHECK_RETRIES=3

docker build \
  --build-arg SERVER_ID="$((RANDOM % 4294967295 + 1))" \
  --tag mysql-server \
  /opt/superset-cluster/mysql-server

docker run \
  --detach \
  --restart always \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --network host \
  --cap-add SYS_NICE \
  --security-opt seccomp=/opt/superset-cluster/mysql-server/seccomp.json \
  --health-cmd "mysqladmin ping" \
  --health-start-period "${HEALTHCHECK_START_PERIOD}s" \
  --health-interval "${HEALTHCHECK_INTERVAL}s" \
  --health-retries ${HEALTHCHECK_RETRIES} \
  --health-timeout "10s" \
  --env MYSQL_INITDB_SKIP_TZINFO="true" \
  --env MYSQL_ROOT_PASSWORD_FILE="/opt/mysql_root_password.txt" \
  mysql-server

sleep ${HEALTHCHECK_START_PERIOD}

for _ in $(seq 1 ${HEALTHCHECK_RETRIES}); do
  if [ "$(docker inspect --format '{{json .State.Health.Status}}' "mysql")" = '"healthy"' ]; then
    docker exec --user=root mysql /bin/bash -c "
      chmod 400 /opt/mysql_root_password.txt \
      && chown --recursive root:root /opt /var/run/mysqld"
  else
    sleep ${HEALTHCHECK_INTERVAL}
  fi
done


#   && chmod -x /usr/bin/kill /usr/bin/killall /usr/bin/pkill /usr/bin/skill \
# /var/lib/mysql
# && chmod 666 /var/lib/mysql/* \
  # && chmod 644 /var/lib/mysql/*ib* /var/lib/mysql/*.pem /var/lib/mysql/*.cnf \