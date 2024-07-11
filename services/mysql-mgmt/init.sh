#!/bin/bash

export IS_PRIMARY_MGMT_NODE="${1}"
export VIRTUAL_IP_ADDRESS="${2}"
export NETWORK_INTERFACE="${3}"
export PRIMARY_MYSQL_NODE="${4}"
export SECONDARY_FIRST_MYSQL_NODE="${5}"
export SECONDARY_SECOND_MYSQL_NODE="${6}"

cd /opt/superset-cluster/mysql-mgmt
docker compose up initcontainer && docker compose up maincontainer --detach

# docker build \
#   --tag mysql-mgmt-initcontainer \
#   /opt/superset-cluster/mysql-mgmt/initcontainer

# docker run \
#   --detach \
#   --name mysql-mgmt-initcontainer \
#   --restart no \
#   --hostname "${HOSTNAME}" \
#   --env IS_PRIMARY_MGMT_NODE="${IS_PRIMARY_MGMT_NODE}" \
#   --env VIRTUAL_IP_ADDRESS="${VIRTUAL_IP_ADDRESS}" \
#   --env NETWORK_INTERFACE="${NETWORK_INTERFACE}" \
#   --env PRIMARY_MYSQL_NODE="${PRIMARY_MYSQL_NODE}" \
#   --env SECONDARY_FIRST_MYSQL_NODE="${SECONDARY_FIRST_MYSQL_NODE}" \
#   --env SECONDARY_SECOND_MYSQL_NODE="${SECONDARY_SECOND_MYSQL_NODE}" \
#   --network host \
#   --privileged \
#   mysql-mgmt-initcontainer


# export IS_PRIMARY_MGMT_NODE=true

# export VIRTUAL_IP_ADDRESS=172.18.0.10

# export NETWORK_INTERFACE=eth0

# export PRIMARY_MYSQL_NODE=node-1

# export SECONDARY_FIRST_MYSQL_NODE=node-2

# export SECONDARY_SECOND_MYSQL_NODE=node-3


# docker exec -it mysql-mgmt-initcontainer bash

# DO DOCKER COMPOSE PREINIT CONTAINER WITH SETUP (NO RESTART) and then main container only with final deamons.

# docker cp initcontainer:/opt/mysql_router/ /opt/superset-cluster/mysql-mgmt
# docker cp initcontainer:/opt/keepalived.conf /opt/superset-cluster/keepalived.conf

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
