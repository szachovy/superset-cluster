#!/bin/bash
# 10.145.211.156 10.145.211.158
# 10.145.211.152 10.145.211.153 10.145.211.154
mgmt_nodes=("wiktor-min-sles" "wiktor-min-rhlike")
mysql_nodes=("wiktor-ctl" "wiktor-srv" "wiktor-pxy")
superset_network_interface="tun0"

virtual_ip_address="10.145.211.155"
virtual_network_interface="eth0"
virtual_ip_address_mask="/16"

_path_to_root_catalog="."

source ${_path_to_root_catalog}/src/common.sh

start_superset() {
  docker network create --opt encrypted --driver overlay --attachable superset-network
  echo $(openssl rand -base64 42) | docker secret create superset_secret_key -
  ./services/redis/init.sh
  ./services/superset/init.sh ${virtual_ip_address}
}

initialize_nodes
superset_node_address=$(get_superset_node_ip ${superset_network_interface})
docker_swarm_token=$(init_and_get_docker_swarm_token ${superset_node_address})
clusterize_nodes
start_superset
