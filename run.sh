
MYSQL_ROOT_PASSWORD=mysql
MYSQL_REPLICAS=3

spawn_environment() {
  docker network create \
    --subnet=172.18.0.0/16 \
    --gateway=172.18.0.1 \
    mysql-network

  docker build \
    --file services/mysql-router/Dockerfile \
    --tag mysql-router \
    .

  docker run \
    --detach \
    --name mysql-router \
    --ip 172.18.0.2 \
    --network mysql-network \
    mysql-router

  for ((replica = 0; replica < $MYSQL_REPLICAS; replica++)); do
    docker run \
      --detach \
      --name mysql-$replica \
      --ip 172.18.0.$((3 + $replica)) \
      --env MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
      --env MYSQL_DATABASE=superset \
      --volume ./src/mysql-config.cnf:/etc/mysql/conf.d/mysql-config.cnf \
      --network mysql-network \
      mysql:latest
    
    sleep 30
    docker exec mysql-router mysqlsh --execute "dba.configureInstance('root@172.18.0.$((3 + $replica)):3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
    docker restart mysql-$replica
    sleep 5
    if [ "$replica" -eq 0 ]; then
      docker exec mysql-router mysqlsh --uri root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --execute "dba.createCluster('mycluster');"
      docker exec mysql-router mysqlrouter --user=root --bootstrap root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --directory /tmp/myrouter --conf-use-sockets --account routerfriend --account-create always
      docker exec mysql-router mysqlrouter -c /tmp/myrouter/mysqlrouter.conf &
    else
      docker exec mysql-router mysqlsh --uri root:$MYSQL_ROOT_PASSWORD@172.18.0.3:3306 --execute "dba.getCluster('mycluster').addInstance('root@172.18.0.$((3 + $replica)):3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false,recoveryMethod:'incremental'});"
    fi
  done

  docker run \
    --detach \
    --name redis \
    --ip 172.18.0.$((3 + $MYSQL_REPLICAS)) \
    --network mysql-network \
    redis:latest

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
