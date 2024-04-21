#!/bin/bash

MYSQL_ROOT_PASSWORD=mysql
MYSQL_REPLICAS=3

spawn_environment() {
  docker network create \
    --subnet=172.18.0.0/16 \
    --gateway=172.18.0.1 \
    mysql-network

  docker build \
    --file services/mysql-mgmt/Dockerfile \
    --tag mysql-mgmt \
    .

  docker run \
    --detach \
    --name mysql-mgmt \
    --ip 172.18.0.2 \
    --network mysql-network \
    mysql-mgmt

  for ((replica = 0; replica < $MYSQL_REPLICAS; replica++)); do
    docker build \
    --file services/mysql-server/Dockerfile \
    --tag mysql-server \
    .

    docker run \
      --detach \
      --name mysql-$replica \
      --ip 172.18.0.$((3 + $replica)) \
      --env MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
      --env MYSQL_DATABASE=superset \
      --volume ./services/mysql-server/mysql_config.cnf:/etc/mysql/conf.d/mysql_config.cnf \
      --network mysql-network \
      mysql-server
    
    sleep 30
    docker exec mysql-mgmt mysqlsh --execute "dba.configureInstance('root@172.18.0.$((3 + $replica)):3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
    docker restart mysql-$replica
    sleep 5
    if [ "$replica" -eq 0 ]; then
      docker exec mysql-mgmt mysqlsh --uri root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --execute "dba.createCluster('mycluster');"
      docker exec mysql-mgmt mysqlrouter --user=root --bootstrap root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --directory /tmp/myrouter --conf-use-sockets --account routerfriend --account-create always
      docker exec mysql-mgmt mysqlrouter -c /tmp/myrouter/mysqlrouter.conf &
    else
      docker exec mysql-mgmt mysqlsh --uri root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --execute "dba.getCluster('mycluster').addInstance('root@172.18.0.$((3 + $replica)):3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false,recoveryMethod:'incremental'});"
    fi
  done

  docker build \
    --file services/redis/Dockerfile \
    --tag redis \
    .

  docker run \
    --detach \
    --name redis \
    --ip 172.18.0.$((3 + $MYSQL_REPLICAS)) \
    --network mysql-network \
    redis

  docker build \
    --file services/superset/Dockerfile \
    --tag superset \
    .

  docker run \
    --detach \
    --name superset \
    --publish 8088:8088 \
    --network mysql-network \
    superset

  docker exec superset superset fab create-admin --username admin --firstname admin --lastname admin --email admin@admin.com --password admin
  docker exec superset superset db upgrade
  docker exec superset superset load_examples
  docker exec superset superset init
}

spawn_environment
