#!/bin/bash

MYSQL_ROOT_PASSWORD=mysql
primary_node_ip="${1}"
docker exec mysql-mgmt mysqlsh --uri root:${MYSQL_ROOT_PASSWORD}@${primary_node_ip}:3306 --execute "dba.createCluster('cluster');"
sleep 15
docker exec mysql-mgmt mysqlrouter --user=root --bootstrap root:${MYSQL_ROOT_PASSWORD}@${primary_node_ip}:3306 --directory /tmp/myrouter --conf-use-sockets --account routerfriend --account-create always
sleep 15

shift
for secondary_node_ip in "$@"; do
  docker exec mysql-mgmt mysqlsh --uri root:${MYSQL_ROOT_PASSWORD}@${primary_node_ip}:3306 --execute "dba.getCluster('cluster').addInstance('root@${secondary_node_ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false,recoveryMethod:'incremental'});"
  sleep 60
done

nohup docker exec mysql-mgmt mysqlrouter -c /tmp/myrouter/mysqlrouter.conf > /dev/null 2>&1 &
