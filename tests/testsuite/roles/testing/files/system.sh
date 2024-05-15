#!/bin/bash

node_prefix="${1}"
nodes="${2}"
network_interface="${3}"

_path_to_root_catalog="../.."

for ((node=0; node < ${nodes}; node++)); do
  if [ ${node} -eq 0 ]; then
    mgmt_nodes=("${node_prefix}-${node}")
  elif [ ${node} -eq $((${nodes}-1)) ]; then
    superset_node="${node_prefix}-${node}"
  else
    mysql_nodes+=("${node_prefix}-${node}")
  fi
done

source "${_path_to_root_catalog}/src/common.sh"

restart_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    docker restart ${mysql_node}
    sleep 10
    nohup ssh root@${mysql_node} "dockerd"  > /dev/null 2>&1 &
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
  ssh root@${superset_node} "cd /opt/superset-cluster && ./services/superset/init.sh $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${mgmt_nodes[0]})"
}
