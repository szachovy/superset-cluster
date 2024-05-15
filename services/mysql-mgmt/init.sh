#!/bin/bash

MYSQL_ROOT_PASSWORD=mysql

docker build \
  --tag mysql-mgmt \
  /opt/superset-cluster/mysql-mgmt

docker run \
  --detach \
  --restart always \
  --name mysql-mgmt \
  --hostname "${HOSTNAME}" \
  --network host \
  mysql-mgmt

for ip in "$@"; do
  docker exec mysql-mgmt mysqlsh --execute "dba.configureInstance('${ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
  sleep 5
done
