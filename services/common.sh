#!/bin/bash

array_to_string_converter() {
  local string_result=""

  for node in "${@}"; do
    string_result+="${node} "
  done
  echo "${string_result}"
}

initialize_nodes() {
  local mgmt_nodes="${1}"
  local mysql_nodes="${2}"

  for mysql_node in "${mysql_nodes[@]}"; do
    scp -r "${path_to_services}/mysql-server" "root@${mysql_node}:/opt"
    ssh root@${mysql_node} "/opt/mysql-server/init.sh"
  done
  for mgmt_node in "${mgmt_nodes[@]}"; do
    scp -r ${path_to_services}/mysql-mgmt "root@${mgmt_node}:/opt"
    ssh root@${mgmt_node} "/opt/mysql-mgmt/init.sh $(array_to_string_converter ${mysql_nodes[@]})"
  done
}

get_supeset_node_ip() {
  local network_interface="${1}"

  eval "echo \$(ifconfig ${network_interface} | awk '/inet / {print \$2}')"
}

get_docker_swarm_token() {
  local superset_node_ip="${1}"

  eval "echo \$(docker swarm init --advertise-addr ${superset_node_ip} | awk '/--token/ {print \$5}')"
}

clusterize_nodes() {
  local mgmt_nodes="${1}"
  local mysql_nodes="${2}"
  local docker_swarm_token="${3}"
  local superset_node_ip="${4}"

  ssh root@${mgmt_nodes[0]} "/opt/mysql-mgmt/clusterize.sh $(array_to_string_converter ${mysql_nodes[@]})"
  ssh root@${mgmt_nodes[0]} "docker swarm join --token ${docker_swarm_token} ${superset_node_ip}:2377"
}
