#!/bin/bash

export IS_PRIMARY_MGMT_NODE="${1}"
export VIRTUAL_IP_ADDRESS="${2}"
export NETWORK_INTERFACE="${3}"
export PRIMARY_MYSQL_NODE="${4}"
export SECONDARY_FIRST_MYSQL_NODE="${5}"
export SECONDARY_SECOND_MYSQL_NODE="${6}"

cd /opt/superset-cluster/mysql-mgmt
docker compose up initcontainer && docker compose up maincontainer --detach

export IS_PRIMARY_MGMT_NODE="true"
export VIRTUAL_IP_ADDRESS="172.18.0.8"
export NETWORK_INTERFACE="eth0"
export PRIMARY_MYSQL_NODE="node-1"
export SECONDARY_FIRST_MYSQL_NODE="node-2"
export SECONDARY_SECOND_MYSQL_NODE="node-3"
