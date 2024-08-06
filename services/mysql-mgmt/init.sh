#!/bin/bash

# export ENVIRONMENT="${1}"
export IS_PRIMARY_MGMT_NODE="${1}"
export VIRTUAL_IP_ADDRESS="${2}"
export VIRTUAL_NETWORK_INTERFACE="${3}"
export PRIMARY_MYSQL_NODE="${4}"
export SECONDARY_FIRST_MYSQL_NODE="${5}"
export SECONDARY_SECOND_MYSQL_NODE="${6}"

docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up initcontainer \
&& \
docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up maincontainer \
  --detach
