#!/bin/bash

MYSQL_ROOT_PASSWORD=mysql
primary_node_ip="${1}"
docker exec mysql-mgmt mysqlsh --uri root:${MYSQL_ROOT_PASSWORD}@${primary_node_ip}:3306 --execute "dba.createCluster('cluster');"
docker exec mysql-mgmt mysqlrouter --user=root --bootstrap root:${MYSQL_ROOT_PASSWORD}@${primary_node_ip}:3306 --directory /tmp/myrouter --conf-use-sockets --account routerfriend --account-create always
docker exec mysql-mgmt mysqlrouter -c /tmp/myrouter/mysqlrouter.conf &

shift
for secondary_node_ip in "$@"; do
  docker exec mysql-mgmt mysqlsh --uri root:${MYSQL_ROOT_PASSWORD}@${primary_node_ip}:3306 --execute "dba.getCluster('cluster').addInstance('root@${secondary_node_ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false,recoveryMethod:'incremental'});"
done

# docker exec mysql-mgmt mysqlsh --uri root:mysql@172.18.0.3:3306 --execute "dba.getCluster('cluster').addInstance('172.18.0.4:3306',{password:'mysql',interactive:false,recoveryMethod:'incremental'});"
# {
#     "clusterName": "cluster", 
#     "defaultReplicaSet": {
#         "name": "default", 
#         "primary": "node-1:3306", 
#         "ssl": "REQUIRED", 
#         "status": "OK_NO_TOLERANCE", 
#         "statusText": "Cluster is NOT tolerant to any failures.", 
#         "topology": {
#             "node-1:3306": {
#                 "address": "node-1:3306", 
#                 "memberRole": "PRIMARY", 
#                 "memberState": "(MISSING)", 
#                 "mode": "n/a", 
#                 "readReplicas": {}, 
#                 "role": "HA", 
#                 "shellConnectError": "MySQL Error 2005: Could not open connection to 'node-1:3306': Unknown MySQL server host 'node-1' (-2)", 
#                 "status": "ONLINE", 
#                 "version": "8.3.0"
#             }
#         }, 
#         "topologyMode": "Single-Primary"
#     }, 
#     "groupInformationSourceMember": "node-1:3306"
# }