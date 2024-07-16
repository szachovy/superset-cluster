#!/bin/bash

export IS_PRIMARY_MGMT_NODE="${1}"
export VIRTUAL_IP_ADDRESS="${2}"
export VIRTUAL_NETWORK_INTERFACE="${3}"
export PRIMARY_MYSQL_NODE="${4}"
export SECONDARY_FIRST_MYSQL_NODE="${5}"
export SECONDARY_SECOND_MYSQL_NODE="${6}"

cd /opt/superset-cluster/mysql-mgmt
docker compose up initcontainer && docker compose up maincontainer --detach
docker compose up initcontainer -d
docker exec -it mysql-mgmt-initcontainer bash
export IS_PRIMARY_MGMT_NODE=true
export VIRTUAL_IP_ADDRESS=10.145.211.155
export VIRTUAL_NETWORK_INTERFACE=eth0
export PRIMARY_MYSQL_NODE=wiktor-ctl
export SECONDARY_FIRST_MYSQL_NODE=wiktor-srv
export SECONDARY_SECOND_MYSQL_NODE=wiktor-pxy

# cd /opt/superset-cluster/mysql-mgmt
# docker compose up initcontainer -d
# docker exec -it mysql-mgmt-initcontainer bash
# docker exec -it mysql bash