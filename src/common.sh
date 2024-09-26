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
  ./${_path_to_root_catalog}/store_credentials.exp ${mysql_nodes[@]} ${_path_to_root_catalog}

  for mysql_node in "${mysql_nodes[@]}"; do
    ssh superset@${mysql_node} "mkdir /opt/superset-cluster"
    scp -r "${_path_to_root_catalog}/services/mysql-server" "superset@${mysql_node}:/opt/superset-cluster"
    ssh superset@${mysql_node} "/opt/superset-cluster/mysql-server/init.sh"
  done

  # VIRTUAL_NETWORK=$(python3 -c "import interfaces; print(interfaces.virtual_network('${virtual_ip_address}','${virtual_ip_address_mask}'))")

  for mgmt_node in "${mgmt_nodes[@]}"; do
    ssh superset@${mgmt_node} "mkdir /opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/mysql-mgmt "superset@${mgmt_node}:/opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/superset "superset@${mgmt_node}:/opt/superset-cluster"
    if [ "${mgmt_node}" = "${mgmt_nodes[0]}" ]; then
      ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address}"
      ssh superset@${mgmt_node} "docker network create --driver overlay --attachable superset-network"
      ssh superset@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh primary ${virtual_ip_address} ${virtual_ip_address_mask} ${virtual_network_interface} ${VIRTUAL_NETWORK} $(array_to_string_converter ${mysql_nodes[@]})"
      ssh superset@${mgmt_node} "docker login ghcr.io -u szachovy -p ..."
      ssh superset@${mgmt_node} "docker pull ghcr.io/szachovy/superset-cluster:latest"
      ssh superset@${mgmt_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
      ssh superset@${mgmt_node} "/opt/superset-cluster/superset/init.sh ${virtual_ip_address} || true"
    else
      ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address}"
      ssh superset@${mgmt_node} "docker network create --driver overlay --attachable superset-network"
      ssh superset@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh secondary ${virtual_ip_address} ${virtual_ip_address_mask} ${virtual_network_interface} ${VIRTUAL_NETWORK} $(array_to_string_converter ${mysql_nodes[@]})"
      ssh superset@${mgmt_node} "docker login ghcr.io -u szachovy -p ..."
      ssh superset@${mgmt_node} "docker pull ghcr.io/szachovy/superset-cluster:latest"
      ssh superset@${mgmt_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
      ssh superset@${mgmt_node} "/opt/superset-cluster/superset/init.sh ${virtual_ip_address} || true"
    fi
  done
}
