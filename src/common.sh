#!/bin/bash

array_to_string_converter() {
  local string_result=""
  for node in "${@}"; do
    string_result+="${node} "
  done
  echo "${string_result}"
}

initialize_nodes() {
  export MYSQL_TEST_LOGIN_FILE="${_path_to_root_catalog}/services/mysql-mgmt/.mylogin.cnf"
  ./${_path_to_root_catalog}/src/store_credentials.exp node-1 node-2 node-3 ${_path_to_root_catalog}
  for mysql_node in "${mysql_nodes[@]}"; do
    ssh superset@${mysql_node} "mkdir --parents /opt/superset-cluster"
    scp -r "${_path_to_root_catalog}/services/mysql-server" "superset@${mysql_node}:/opt/superset-cluster"
    ssh superset@${mysql_node} "/opt/superset-cluster/mysql-server/init.sh"
    # ssh superset@${mysql_node} "rm /opt/superset-cluster/mysql-server/mysql_root_password.txt"
    # ssh superset@${mysql_node} "docker cp mysql:/opt/.mylogin.cnf /opt/superset-cluster/mysql-server/"
    # scp "superset@${mysql_node}:/opt/superset-cluster/mysql-server/.mylogin.cnf" "${_path_to_root_catalog}/services/mysql-server/"
  done
  # # mv "${_path_to_root_catalog}/services/mysql-server/.mylogin.cnf" "${_path_to_root_catalog}/services/mysql-mgmt/"
  IS_PRIMARY_MGMT_NODE=true
  for mgmt_node in "${mgmt_nodes[@]}"; do
    ssh superset@${mgmt_node} "mkdir --parents /opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/mysql-mgmt "superset@${mgmt_node}:/opt/superset-cluster"
    ssh superset@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh ${ENVIRONMENT} ${IS_PRIMARY_MGMT_NODE} ${virtual_ip_address} ${virtual_network_interface} $(array_to_string_converter ${mysql_nodes[@]})"
    IS_PRIMARY_MGMT_NODE=false
  done
}

get_superset_node_ip() {
  local superset_network_interface="${1}"
  python3 -c "import src.interfaces; print(src.interfaces.network_interfaces(network_interface='${superset_network_interface}'))"
}

init_and_get_docker_swarm_token() {
  local superset_node_address="${1}"
  eval "echo \$(docker swarm init --advertise-addr ${superset_node_address} | awk '/--token/ {print \$5}')"
}

clusterize_nodes() {
  ssh superset@${mgmt_nodes[0]} "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
  ssh superset@${mgmt_nodes[1]} "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
}
