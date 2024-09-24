#!/bin/bash
# 10.145.211.156 10.145.211.158
# 10.145.211.152 10.145.211.153 10.145.211.154
mgmt_nodes=("wiktor-min-deblike" "wiktor-min-rhlike")
mysql_nodes=("wiktor-min-build" "wiktor-cli-sles" "wiktor-minssh-sles")
superset_network_interface="enp1s0"

virtual_ip_address="10.145.211.155"
virtual_network_interface="ens3"
virtual_ip_address_mask="22"

_path_to_root_catalog="."

source ${_path_to_root_catalog}/src/common.sh

# docker_swarm_token() {
#   local superset_node_address="${1}"
#   ssh superset@${superset_node} "$(typeset -f init_and_get_docker_swarm_token); init_and_get_docker_swarm_token ${superset_node_address}"
# }

# start_superset() {
#   scp -r ${_path_to_root_catalog}/services "superset@${superset_node}:/opt/superset-cluster"
#   ssh superset@${superset_node} "cd /opt/superset-cluster && ./services/superset/init.sh ${virtual_ip_address}"
# }

# superset_node="wiktor-min-deblike.mgr.suse.de"
# superset_node_address="10.145.211.159"
# docker_swarm_token=$(docker_swarm_token "${superset_node_address}")
# ssh superset@${superset_node} "docker network create --driver overlay --attachable superset-network"
# ssh superset@${superset_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
# ssh superset@${superset_node} "docker node update --label-add preferred=false ${mgmt_nodes[1]}"
clusterize_nodes
initialize_nodes
start_superset
# --opt encrypted 
# superset_node_address=$(get_superset_node_ip ${superset_network_interface})
# docker_swarm_token=$(init_and_get_docker_swarm_token ${superset_node_address})
# docker network create --driver overlay --attachable superset-network
# clusterize_nodes
# echo $(openssl rand -base64 42) | docker secret create superset_secret_key -
# initialize_nodes
# ./services/superset/init.sh ${virtual_ip_address}
# --opt encrypted 