#!/bin/bash

export MGMT_NODE_TYPE="${1}"
export VIRTUAL_IP_ADDRESS="${2}"
export VIRTUAL_IP_ADDRESS_MASK="${3}"
export VIRTUAL_NETWORK_INTERFACE="${4}"
export VIRTUAL_NETWORK="${5}"
export PRIMARY_MYSQL_NODE="${6}"
export SECONDARY_FIRST_MYSQL_NODE="${7}"
export SECONDARY_SECOND_MYSQL_NODE="${8}"
export HEALTHCHECK_START_PERIOD=25  # must be greater than vrrp_startup_delay
export HEALTHCHECK_INTERVAL=5
export HEALTHCHECK_RETRIES=3

openssl \
  genpkey \
    -algorithm RSA \
    -out "/opt/superset-cluster/mysql-mgmt/mysql_router_${MGMT_NODE_TYPE}_key.pem"

openssl \
  req \
    -new \
    -key "/opt/superset-cluster/mysql-mgmt/mysql_router_${MGMT_NODE_TYPE}_key.pem" \
    -out "/opt/superset-cluster/mysql-mgmt/mysql_router_${MGMT_NODE_TYPE}_certificate_signing_request.pem" \
    -subj "/CN=Superset-Cluster-MySQL-Router-${MGMT_NODE_TYPE}"

openssl \
  x509 \
    -in "/opt/superset-cluster/mysql-mgmt/mysql_router_${MGMT_NODE_TYPE}_certificate_signing_request.pem" \
    -CA "/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_certificate.pem" \
    -CAkey "/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_key.pem" \
    -CAcreateserial \
    -out "/opt/superset-cluster/mysql-mgmt/mysql_router_${MGMT_NODE_TYPE}_certificate.pem" \
    -req \
    -days 365

docker run \
  --detach \
  --restart always \
  --name redis \
  --hostname redis \
  --network superset-network \
  redis
  #   --publish 6379:6379 \
  # --network host \
  

docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up initcontainer \
&& \
docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up maincontainer \
  --detach

# export MGMT_NODE_TYPE="primary"
# export VIRTUAL_IP_ADDRESS="10.145.211.155"
# export VIRTUAL_IP_ADDRESS_MASK="255.255.0.0"
# export VIRTUAL_NETWORK_INTERFACE="ens3"
# export VIRTUAL_NETWORK="10.145.208.0/22"
# export PRIMARY_MYSQL_NODE="wiktor-min-build"
# export SECONDARY_FIRST_MYSQL_NODE="wiktor-srv"
# export SECONDARY_SECOND_MYSQL_NODE="wiktor-pxy"
# export HEALTHCHECK_START_PERIOD=90
