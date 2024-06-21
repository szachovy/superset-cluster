#!/bin/bash

mgmt_nodes=("10.145.211.152")
mysql_nodes=("10.145.211.156" "10.145.211.154" "10.145.211.153")
network_interface="tun0"

_path_to_root_catalog="."
preload_examples=false

source ${_path_to_root_catalog}/src/common.sh

restart_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    ssh root@${mysql_node} "docker restart mysql"
  done
}

start_superset() {
  docker network create --driver overlay --attachable superset-network
  ./services/redis/init.sh
  ./services/superset/init.sh ${mgmt_nodes[0]} ${preload_examples}
}

initialize_nodes
restart_nodes
superset_node_address=$(get_superset_node_ip ${network_interface})
docker_swarm_token=$(init_and_get_docker_swarm_token ${superset_node_address})
clusterize_nodes
start_superset
