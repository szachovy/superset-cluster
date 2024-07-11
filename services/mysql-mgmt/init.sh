#!/bin/bash

docker build \
  --tag mysql-mgmt \
  /opt/superset-cluster/mysql-mgmt

docker run \
  --detach \
  --name mysql-mgmt \
  --restart always \
  --hostname "${HOSTNAME}" \
  --env IS_SETUP="${1}" \
  --env IS_PRIMARY_MGMT_NODE="${2}" \
  --env VIRTUAL_IP_ADDRESS="${3}" \
  --env NETWORK_INTERFACE="${4}" \
  --env PRIMARY_MYSQL_NODE="${5}" \
  --env SECONDARY_FIRST_MYSQL_NODE="${6}" \
  --env SECONDARY_SECOND_MYSQL_NODE="${7}" \
  --network host \
  --privileged \
  mysql-mgmt

DO DOCKER COMPOSE PREINIT CONTAINER WITH SETUP (NO RESTART) and then main container only with final deamons.

docker cp mysql-mgmt:/opt/mysql_router/ /opt/superset-cluster/mysql-mgmt

# sleep 15
# for ip in "$@"; do
#   docker exec mysql-mgmt mysqlsh --execute "dba.configureInstance('${ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
#   sleep 15
# done

# docker run \
#   --detach \
#   --restart always \
#   --name mysql-mgmt \
#   --hostname "${HOSTNAME}" \
#   --env IS_SETUP="false" \
#   --env IS_PRIMARY_MGMT_NODE="true" \
#   --env VIRTUAL_IP_ADDRESS="172.18.0.10" \
#   --env NETWORK_INTERFACE="eth0" \
#   --env PRIMARY_MYSQL_NODE="node-1" \
#   --env SECONDARY_FIRST_MYSQL_NODE="node-2" \
#   --env SECONDARY_SECOND_MYSQL_NODE="node-3" \
#   --network host \
#   --privileged \
#   mysql-mgmt

# docker build \
#   --build-arg SUPERSET_USER_PASSWORD="mysql" \
#   --build-arg IS_PRIMARY_MGMT_NODE="true" \
#   --build-arg VIRTUAL_IP_ADDRESS="172.18.0.10" \
#   --build-arg NETWORK_INTERFACE="eth0" \
#   --build-arg MYSQL_NODES="node-1 node-2 node-3" \
#   --tag mysql-mgmt \
#   /opt/superset-cluster/mysql-mgmt
