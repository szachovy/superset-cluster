#!/bin/bash

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
