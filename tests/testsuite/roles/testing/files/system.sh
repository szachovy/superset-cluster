#!/bin/bash

node_prefix="${1}"
network_interface="${2}"

mgmt_nodes=("${node_prefix}-0" "${node_prefix}-5")
mysql_nodes=("${node_prefix}-1" "${node_prefix}-2" "${node_prefix}-3")
superset_node="${node_prefix}-4"

_path_to_root_catalog="../.."
preload_examples=true
keepalive_ip="172.18.0.10"

source "${_path_to_root_catalog}/src/common.sh"

restart_nodes() {
  sleep 60
  for mysql_node in "${mysql_nodes[@]}"; do
    docker restart ${mysql_node}
    sleep 60
    nohup ssh root@${mysql_node} "service docker start"  > /dev/null 2>&1 &
  done
}

superset_node_address() {
  ssh root@"${superset_node}" "cd /opt/superset-cluster; $(typeset -f get_superset_node_ip); get_superset_node_ip ${network_interface}"
}

docker_swarm_token() {
  local superset_node_address="${1}"
  ssh root@"${superset_node}" "$(typeset -f init_and_get_docker_swarm_token); init_and_get_docker_swarm_token ${superset_node_address}"
}

start_superset() {
  ssh root@${superset_node} "docker network create --driver overlay --attachable superset-network"
  scp -r ${_path_to_root_catalog}/services "root@${superset_node}:/opt/superset-cluster"
  ssh root@${superset_node} "cd /opt/superset-cluster && ./services/redis/init.sh"
  ssh root@${superset_node} "cd /opt/superset-cluster && ./services/superset/init.sh ${keepalive_ip} ${preload_examples}"
}
