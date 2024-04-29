#!/bin/bash

# currently using virtual environment
# cd tests
# ./setup/setup.sh 4
# cd ..
# -----------------------------

# to be removed after cmd parsing
mgmt_nodes=(10.145.211.152)
# mysql_nodes=(172.18.0.3 172.18.0.4 172.18.0.5)
mysql_nodes=(10.145.211.153 10.145.211.154 10.145.211.156)
# -----------------------------

initialize_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    scp -r services/mysql-server "root@${mysql_node}:/opt"
    ssh root@${mysql_node} "/opt/mysql-server/init.sh"
  done
  for mgmt_node in "${mgmt_nodes[@]}"; do
    scp -r services/mysql-mgmt "root@${mgmt_node}:/opt"
    
    tmp_args="10.145.211.153 10.145.211.154 10.145.211.156"
    ssh root@${mgmt_node} "/opt/mysql-mgmt/init.sh ${tmp_args}"
  done
}

restart_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    ssh root@${mysql_node} "reboot"
  done
  sleep 200
}

clusterize_nodes() {
  tmp_args="10.145.211.153 10.145.211.154 10.145.211.156"
  ssh root@${mgmt_nodes[0]} "/opt/mysql-mgmt/clusterize.sh ${tmp_args}"

  tun_ip=$(ifconfig tun0 | awk '/inet / {print $2}')
  token=$(docker swarm init --advertise-addr ${tun_ip} | awk '/--token/ {print $5}')
  docker network create --driver overlay --attachable superset-network
  ssh root@${mgmt_nodes[0]} "docker swarm join --token ${token} ${tun_ip}:2377"
  # ssh root@${mgmt_nodes[1]} ...
}

start_superset() {
  ./services/redis/init.sh
  ./services/superset/init.sh
}

initialize_nodes
restart_nodes
clusterize_nodes
start_superset
