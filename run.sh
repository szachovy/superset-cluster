#!/bin/bash

# currently using virtual environment
cd tests
./setup/setup.sh 4
cd ..
# -----------------------------

# to be removed after cmd parsing
mgmt_nodes=(172.18.0.2)
mysql_nodes=(172.18.0.3 172.18.0.4 172.18.0.5)
tmp_args=""
# -----------------------------

initialize_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    scp -r services/mysql-server "root@${mysql_node}:/opt"
    ssh root@${mysql_node} "/opt/mysql-server/init.sh"
    tmp_args+="$mysql_node "
  done
  for mgmt_node in "${mgmt_nodes[@]}"; do
    scp -r services/mysql-mgmt "root@${mgmt_node}:/opt"
    ssh root@${mgmt_node} "/opt/mysql-mgmt/init.sh ${tmp_args}"
  done
}

restart_nodes() {
  # reboot for standalone nodes
  # for mysql_node in "${mysql_nodes[@]}"; do
  #   ssh root@${mysql_node} "reboot"
  # done
  docker restart node-1
  sleep 5
  nohup ssh root@172.18.0.3 "dockerd"  > /dev/null 2>&1 &

  docker restart node-2
  sleep 5
  nohup ssh root@172.18.0.4 "dockerd" > /dev/null 2>&1 &

  docker restart node-3
  sleep 5
  nohup ssh root@172.18.0.5 "dockerd" > /dev/null 2>&1 &
}

clusterize_nodes() {
  ssh root@${mgmt_nodes[0]} "/opt/mysql-mgmt/clusterize.sh ${tmp_args}"
  # ssh root@${mgmt_nodes[1]} ...
}

start_superset() {
  docker network create superset-network
  ./services/redis/init.sh
  ./services/superset/init.sh
}

initialize_nodes
restart_nodes
clusterize_nodes
start_superset
