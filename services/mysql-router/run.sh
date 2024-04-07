docker build ./services/mysql-router/ -t mysql-router

docker run -it \
  -e MYSQL_HOST=172.18.0.2 \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=mysql \
  -e MYSQL_INNODB_CLUSTER_MEMBERS=3 \
  -e MYSQL_ROUTER_BOOTSTRAP_EXTRA_OPTIONS="--conf-use-sockets --conf-use-gr-notifications" \
  --network mysql-network \
  mysql-router /bin/bash

# container-registry.oracle.com/mysql/community-router
