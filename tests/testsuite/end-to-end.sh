#!/bin/bash

source ../services/common.sh

# mgmt_nodes=("172.18.0.2")
# mysql_nodes=("172.18.0.3" "172.18.0.4" "172.18.0.5")
# superset_node="172.18.0.6"

mgmt_nodes=("node-0")
mysql_nodes=("node-1" "node-2" "node-3")
superset_node="node-4"

path_to_services="../services"
network_interface="eth0"

restart_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    docker restart ${mysql_node}
    sleep 10
    nohup ssh root@${mysql_node} "dockerd"  > /dev/null 2>&1 &
  done
}

start_superset() {
  ssh root@${superset_node} "docker network create --driver overlay --attachable superset-network"
  scp -r ${path_to_services} "root@${superset_node}:/opt"
  ssh root@${superset_node} "cd /opt && ./services/redis/init.sh"
  ssh root@${superset_node} "cd /opt && ./services/superset/init.sh $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${mgmt_nodes[0]})"
}

initialize_nodes
restart_nodes
superset_node_address=$(ssh root@${superset_node} "$(typeset -f get_superset_node_ip); get_superset_node_ip ${network_interface}")
docker_swarm_token=$(ssh root@${superset_node} "$(typeset -f init_and_get_docker_swarm_token); init_and_get_docker_swarm_token ${superset_node_address}")
clusterize_nodes
start_superset
