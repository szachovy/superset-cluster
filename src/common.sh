#!/bin/bash

array_to_string_converter() {
  local string_result=""
  for node in "${@}"; do
    string_result+="${node} "
  done
  echo "${string_result}"
}

initialize_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    ssh root@${mysql_node} "mkdir --parents /opt/superset-cluster"
    scp -r "${_path_to_root_catalog}/services/mysql-server" "root@${mysql_node}:/opt/superset-cluster"
    ssh root@${mysql_node} "/opt/superset-cluster/mysql-server/init.sh"
  done
  for mgmt_node in "${mgmt_nodes[@]}"; do
    ssh root@${mgmt_node} "mkdir --parents /opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/mysql-mgmt "root@${mgmt_node}:/opt/superset-cluster"
    ssh root@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh $(array_to_string_converter ${mysql_nodes[@]})"
  done
}

get_superset_node_ip() {
  local network_interface="${1}"
  python3 -c "import src.interfaces; print(src.interfaces.network_interfaces(network_interface='${network_interface}'))"
}

init_and_get_docker_swarm_token() {
  local superset_node_address="${1}"
  eval "echo \$(docker swarm init --advertise-addr ${superset_node_address} | awk '/--token/ {print \$5}')"
}

clusterize_nodes() {
  ssh root@${mgmt_nodes[0]} "/opt/superset-cluster/mysql-mgmt/clusterize.sh $(array_to_string_converter ${mysql_nodes[@]})"
  ssh root@${mgmt_nodes[0]} "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
}
