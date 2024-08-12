#!/bin/bash

node_prefix="${1}"
superset_network_interface="${2}"
virtual_ip_address="${3}"
virtual_ip_address_mask="${4}"
virtual_network_interface="${5}"

mgmt_nodes=("${node_prefix}-0" "${node_prefix}-5")
mysql_nodes=("${node_prefix}-1" "${node_prefix}-2" "${node_prefix}-3")
superset_node="${node_prefix}-4"

_path_to_root_catalog="../.."

source "${_path_to_root_catalog}/src/common.sh"

superset_node_address() {
  ssh superset@"${superset_node}" "cd /opt/superset-cluster; $(typeset -f get_superset_node_ip); get_superset_node_ip ${superset_network_interface}"
}

docker_swarm_token() {
  local superset_node_address="${1}"
  ssh superset@"${superset_node}" "$(typeset -f init_and_get_docker_swarm_token); init_and_get_docker_swarm_token ${superset_node_address}"
}

start_superset() {
  ssh superset@${superset_node} "docker network create --opt encrypted --driver overlay --attachable superset-network"
  ssh superset@${superset_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
  scp -r ${_path_to_root_catalog}/services "superset@${superset_node}:/opt/superset-cluster"
  ssh superset@${superset_node} "cd /opt/superset-cluster && ./services/redis/init.sh"
  ssh superset@${superset_node} "cd /opt/superset-cluster && ./services/superset/init.sh ${virtual_ip_address}"
}
