#!/bin/bash

MYSQL_ROOT_PASSWORD=mysql

docker build \
  --tag mysql-mgmt \
  /opt/mysql-mgmt

docker run \
  --detach \
  --restart always \
  --name mysql-mgmt \
  --hostname "${HOSTNAME}" \
  --network host \
  --publish 6446:6446 \
  mysql-mgmt

for ip in "$@"; do
  docker exec mysql-mgmt mysqlsh --execute "dba.configureInstance('${ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
done

# docker exec mysql-mgmt mysqlsh --uri root:mysql@172.18.0.3:3306 --sql --execute="SELECT @@hostname;"

# mysql_nodes=172.18.0.3,172.18.0.4,172.18.0.5

# docker exec mysqlsh --execute "dba.configureInstance('${1}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
# docker restart mysql-$replica

# for ip in "$@"; do
  
# done

#     sleep 5
#     if [ "$replica" -eq 0 ]; then
#       docker exec mysql-mgmt mysqlsh --uri root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --execute "dba.createCluster('mycluster');"
#       docker exec mysql-mgmt mysqlrouter --user=root --bootstrap root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --directory /tmp/myrouter --conf-use-sockets --account routerfriend --account-create always
#       docker exec mysql-mgmt mysqlrouter -c /tmp/myrouter/mysqlrouter.conf &
#     else
#       docker exec mysql-mgmt mysqlsh --uri root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --execute "dba.getCluster('mycluster').addInstance('root@172.18.0.$((3 + $replica)):3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false,recoveryMethod:'incremental'});"