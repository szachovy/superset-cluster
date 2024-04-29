#!/bin/bash

mgmt_nodes=(10.145.211.152)
mysql_nodes=(10.145.211.153 10.145.211.154 10.145.211.156)

ssh root@${mgmt_nodes[0]} "docker stop mysql-mgmt && docker rm mysql-mgmt && docker swarm leave"
for mysql_node in "${mysql_nodes[@]}"; do
  ssh root@${mysql_node} "docker stop mysql && docker rm mysql"
done
docker stop redis
docker rm redis
docker stop superset
docker rm superset
docker swarm leave --force
