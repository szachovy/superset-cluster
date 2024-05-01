#!/bin/bash

# source ../../services/common.sh

mgmt_nodes=("172.18.0.2")
mysql_nodes=("172.18.0.3" "172.18.0.4" "172.18.0.5")
superset_node="172.18.0.6"

path_to_services="../services"
network_interface="eth0"

array_to_string_converter() {
  local string_result=""
  for node in "${@}"; do
    string_result+="${node} "
  done
  echo "${string_result}"
}

initialize_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    scp -r "${path_to_services}/mysql-server" "root@${mysql_node}:/opt"
    ssh root@${mysql_node} "/opt/mysql-server/init.sh"
  done
  for mgmt_node in "${mgmt_nodes[@]}"; do
    scp -r ${path_to_services}/mysql-mgmt "root@${mgmt_node}:/opt"
    ssh root@${mgmt_node} "/opt/mysql-mgmt/init.sh $(array_to_string_converter ${mysql_nodes[@]})"
  done
}

restart_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    docker restart $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}} {{.Name}}' $(docker ps -q) | grep ${mysql_node} | awk '{print $2}')
    sleep 10
    nohup ssh root@${mysql_node} "dockerd"  > /dev/null 2>&1 &
  done
}

get_superset_node_ip() {
  local network_interface="${1}"
  eval "echo \$(ifconfig ${network_interface} | awk '/inet / {print \$2}')"
}

init_and_get_docker_swarm_token() {
  local superset_node_address="${1}"
  eval "echo \$(docker swarm init --advertise-addr ${superset_node_address} | awk '/--token/ {print \$5}')"
}

clusterize_nodes() {
  ssh root@${mgmt_nodes[0]} "/opt/mysql-mgmt/clusterize.sh $(array_to_string_converter ${mysql_nodes[@]})"
  # superset_node_ip=$(ssh root@${superset_node} "echo \$(ifconfig ${ip_address} | awk '/inet / {print \$2}')")
  # docker_swarm_token=$(ssh root@${superset_node} "echo \$(docker swarm init --advertise-addr ${superset_node_ip} | awk '/--token/ {print \$5}')")
  ssh root@${mgmt_nodes[0]} "docker swarm join --token ${docker_swarm_token} ${superset_node_ip}:2377"
}

start_superset() {
  ssh root@${superset_node} "docker network create --driver overlay --attachable superset-network"
  scp -r ${path_to_services} "root@${superset_node}:/opt"
  ssh root@${superset_node} "cd /opt && ./services/redis/init.sh"
  ssh root@${superset_node} "cd /opt && ./services/superset/init.sh ${mgmt_nodes[0]}"
}

initialize_nodes
restart_nodes
superset_node_address=$(ssh root@${superset_node} "$(typeset -f get_superset_node_ip); get_superset_node_ip ${network_interface}")
docker_swarm_token=$(ssh root@${superset_node} "$(typeset -f init_and_get_docker_swarm_token); init_and_get_docker_swarm_token ${superset_node_address}")
clusterize_nodes
start_superset
