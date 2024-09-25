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

  # export PYTHONPATH="${PYTHONPATH}:${_path_to_root_catalog}"  # Delete it later
  # VIRTUAL_NETWORK=$(python3 -c "import interfaces; print(interfaces.virtual_network('${virtual_ip_address}','${virtual_ip_address_mask}'))")
  VIRTUAL_NETWORK="172.18.0.0/16"
  # VIRTUAL_NETWORK="10.145.208.0/22"

  for mgmt_node in "${mgmt_nodes[@]}"; do
    ssh superset@${mgmt_node} "mkdir /opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/mysql-mgmt "superset@${mgmt_node}:/opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/superset "superset@${mgmt_node}:/opt/superset-cluster"
    if [ "${mgmt_node}" = "${mgmt_nodes[0]}" ]; then
      ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address}"
      ssh superset@${mgmt_node} "docker network create --driver overlay --attachable superset-network"
      ssh superset@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh primary ${virtual_ip_address} ${virtual_ip_address_mask} ${virtual_network_interface} ${VIRTUAL_NETWORK} $(array_to_string_converter ${mysql_nodes[@]})"
      # ssh superset@${superset_node} "docker node update --label-add preferred=true ${mgmt_node}"
      # docker node update --label-add preferred=true ${mgmt_node}
      # docker_swarm_token=$(ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address} | awk '/--token/ {print \$5}'")
      ssh superset@${mgmt_node} "docker login ghcr.io -u szachovy -p ..."
      ssh superset@${mgmt_node} "docker pull ghcr.io/szachovy/superset-cluster:latest"
      # ssh superset@${mgmt_node} "docker network create --opt encrypted --driver overlay --attachable superset-network"
      ssh superset@${mgmt_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
      ssh superset@${mgmt_node} "/opt/superset-cluster/superset/init.sh ${virtual_ip_address}"
    else
      ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address}"
      ssh superset@${mgmt_node} "docker network create --driver overlay --attachable superset-network"
      ssh superset@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh secondary ${virtual_ip_address} ${virtual_ip_address_mask} ${virtual_network_interface} ${VIRTUAL_NETWORK} $(array_to_string_converter ${mysql_nodes[@]})"
      # ssh superset@${mgmt_node} "docker swarm join --token ${docker_swarm_token} ${virtual_ip_address}:2377"
      # ssh superset@${mgmt_nodes[0]} "docker node promote ${mgmt_nodes[1]}"
      ssh superset@${mgmt_node} "docker login ghcr.io -u szachovy -p ..."
      ssh superset@${mgmt_node} "docker pull ghcr.io/szachovy/superset-cluster:latest"
      ssh superset@${mgmt_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
      ssh superset@${mgmt_node} "/opt/superset-cluster/superset/init.sh ${virtual_ip_address} || true"
    fi
  done
}

# get_superset_node_ip() {
#   local superset_network_interface="${1}"
#   python3 -c "import src.interfaces; print(src.interfaces.network_interfaces(network_interface='${superset_network_interface}'))"
# }

# init_and_get_docker_swarm_token() {
#   local superset_node_address="${1}"
#   eval "echo \$(docker swarm init --advertise-addr ${superset_node_address} | awk '/--token/ {print \$5}')"
# }

# clusterize_nodes() {
#   ssh superset@${mgmt_nodes[0]} "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
#   ssh superset@${mgmt_nodes[1]} "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
# }

# clusterize_nodes() {
#   cp -r "${_path_to_root_catalog}/services/superset" "/opt/superset-cluster-service"
#   cp -r "${_path_to_root_catalog}/src" "/opt/superset-cluster-service/src"  # integrate to superset service later
#   # local superset_network_interface="${1}"
#   # cd /opt/superset-cluster-service
#   export PYTHONPATH=${PYTHONPATH:-}/opt/superset-cluster-service
#   superset_node_address=$(echo $(python3 -c "import src.interfaces; print(src.interfaces.network_interfaces(network_interface='${superset_network_interface}'))"))
#   docker_swarm_token=$(eval "echo \$(docker swarm init --advertise-addr ${superset_node_address} | awk '/--token/ {print \$5}')")
#   ssh superset@${mgmt_nodes[0]} "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
#   ssh superset@${mgmt_nodes[1]} "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
#   docker pull ghcr.io/szachovy/superset-cluster:latest
# }

# start_superset() {
#   docker network create --opt encrypted --driver overlay --attachable superset-network
#   echo $(openssl rand -base64 42) | docker secret create superset_secret_key -
#   /opt/superset-cluster-service/init.sh ${virtual_ip_address}
# }

# ssh superset@node-0 "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"
# ssh superset@node-1 "docker swarm join --token ${docker_swarm_token} ${superset_node_address}:2377"