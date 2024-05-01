#!/bin/bash

mgmt_nodes=("172.18.0.2")
mysql_nodes=("172.18.0.3" "172.18.0.4" "172.18.0.5")
superset_node="172.18.0.6"

initialize_nodes() {
  for mysql_node in "${mysql_nodes[@]}"; do
    scp -r ../services/mysql-server "root@${mysql_node}:/opt"
    ssh root@${mysql_node} "/opt/mysql-server/init.sh"
  done
  for mgmt_node in "${mgmt_nodes[@]}"; do
    scp -r ../services/mysql-mgmt "root@${mgmt_node}:/opt"
    
    tmp_args="10.145.211.153 10.145.211.154 10.145.211.156"
    ssh root@${mgmt_node} "/opt/mysql-mgmt/init.sh ${tmp_args}"
  done
  scp -r ../services "root@${superset_node}:/opt"
}

copy_content() {
  scp -r ../services/mysql-mgmt "root@172.18.0.2:/opt"
  scp -r ../services/mysql-server "root@172.18.0.3:/opt"
  scp -r ../services/mysql-server "root@172.18.0.4:/opt"
  scp -r ../services/mysql-server "root@172.18.0.5:/opt"
  scp -r ../services "root@172.18.0.6:/opt"
}

initialize_nodes() {
  ssh root@172.18.0.3 "/opt/mysql-server/init.sh"
  ssh root@172.18.0.4 "/opt/mysql-server/init.sh"
  ssh root@172.18.0.5 "/opt/mysql-server/init.sh"
  ssh root@172.18.0.2 "/opt/mysql-mgmt/init.sh 172.18.0.3 172.18.0.4 172.18.0.5"
}

restart_nodes() {
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
  ssh root@172.18.0.2 "/opt/mysql-mgmt/clusterize.sh 172.18.0.3 172.18.0.4 172.18.0.5"
}

start_superset() {
  ssh root@172.18.0.6 "docker network create superset-network"
  ssh root@172.18.0.6 "cd /opt && /opt/services/redis/init.sh"
  ssh root@172.18.0.6 "cd /opt && /opt/services/superset/init.sh"
}

copy_content
initialize_nodes
restart_nodes
clusterize_nodes
start_superset
