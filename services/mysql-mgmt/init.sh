#!/bin/bash

export ENVIRONMENT="${1}"
export IS_PRIMARY_MGMT_NODE="${2}"
export VIRTUAL_IP_ADDRESS="${3}"
export VIRTUAL_NETWORK_INTERFACE="${4}"
export PRIMARY_MYSQL_NODE="${5}"
export SECONDARY_FIRST_MYSQL_NODE="${6}"
export SECONDARY_SECOND_MYSQL_NODE="${7}"

docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up initcontainer \
&& \
docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up maincontainer \
  --detach
# docker compose up initcontainer -d
# docker exec -it mysql-mgmt-initcontainer bash
# docker exec -it mysql-mgmt bash
# docker image rm mysql-mgmt
# ip addr add 192.168.1.100/24 dev eth0


# export ENVIRONMENT=testing
# export IS_PRIMARY_MGMT_NODE=true
# export VIRTUAL_IP_ADDRESS=172.18.0.8
# export VIRTUAL_NETWORK_INTERFACE=eth0
# export PRIMARY_MYSQL_NODE=node-1
# export SECONDARY_FIRST_MYSQL_NODE=node-2
# export SECONDARY_SECOND_MYSQL_NODE=node-3

# cd /opt/superset-cluster/mysql-mgmt
# docker compose up initcontainer -d
# docker exec -it mysql-mgmt-initcontainer bash
# docker exec -it mysql bash