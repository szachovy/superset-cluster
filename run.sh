#!/bin/bash
# 10.145.211.156 10.145.211.158
# 10.145.211.152 10.145.211.153 10.145.211.154
mgmt_nodes=("wiktor-min-sles" "wiktor-min-rhlike")
mysql_nodes=("wiktor-ctl" "wiktor-srv" "wiktor-pxy")
superset_network_interface="tun0"

virtual_ip_address="10.145.211.155"
virtual_network_interface="eth0"

_path_to_root_catalog="."
preload_examples=false

source ${_path_to_root_catalog}/src/common.sh

start_superset() {
  docker network create --driver overlay --attachable superset-network
  ./services/redis/init.sh
  ./services/superset/init.sh ${virtual_ip_address} ${preload_examples}
}

initialize_nodes
# superset_node_address=$(get_superset_node_ip ${superset_network_interface})
# docker_swarm_token=$(init_and_get_docker_swarm_token ${superset_node_address})
# clusterize_nodes
# start_superset
