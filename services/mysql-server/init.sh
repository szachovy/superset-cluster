#!/bin/bash

docker build \
  --build-arg SERVER_ID=$((RANDOM % 4294967295 + 1)) \
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
  --env MYSQL_INITDB_SKIP_TZINFO="true" \
  --env MYSQL_ROOT_PASSWORD_FILE="/opt/mysql_root_password.txt" \
  mysql-server

# mysqladmin ping
# https://serverfault.com/questions/999111/check-if-mysql-server-is-alive

docker exec --user=root mysql /bin/bash -c "
  chmod 400 /opt/mysql_root_password.txt \
  && chown --recursive root:root /opt /var/run/mysqld"

#   && chmod -x /usr/bin/kill /usr/bin/killall /usr/bin/pkill /usr/bin/skill \
# /var/lib/mysql
# && chmod 666 /var/lib/mysql/* \
  # && chmod 644 /var/lib/mysql/*ib* /var/lib/mysql/*.pem /var/lib/mysql/*.cnf \