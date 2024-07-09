#!/bin/bash

docker build \
  --build-arg SUPERSET_USER_PASSWORD="${1}" \
  --build-arg IS_PRIMARY_MGMT_NODE="${2}" \
  --build-arg VIRTUAL_IP_ADDRESS="${3}" \
  --build-arg NETWORK_INTERFACE="${4}" \
  --build-arg MYSQL_NODES="${5} ${6} ${7}" \
  --tag mysql-mgmt \
  /opt/superset-cluster/mysql-mgmt

docker run \
  --detach \
  --restart always \
  --name mysql-mgmt \
  --hostname "${HOSTNAME}" \
  --network host \
  --privileged \
  mysql-mgmt

# sleep 15
# for ip in "$@"; do
#   docker exec mysql-mgmt mysqlsh --execute "dba.configureInstance('${ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
#   sleep 15
# done

docker build \
  --build-arg SUPERSET_USER_PASSWORD="mysql" \
  --build-arg IS_PRIMARY_MGMT_NODE="true" \
  --build-arg VIRTUAL_IP_ADDRESS="172.18.0.10" \
  --build-arg NETWORK_INTERFACE="eth0" \
  --build-arg MYSQL_NODES="node-1 node-2 node-3" \
  --tag mysql-mgmt \
  /opt/superset-cluster/mysql-mgmt
