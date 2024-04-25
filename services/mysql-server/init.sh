MYSQL_ROOT_PASSWORD=mysql

docker build \
  --build-arg MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
  --build-arg MYSQL_DATABASE=superset \
  --tag mysql-server \
  /opt/mysql-server

docker run \
  --detach \
  --restart always \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --network host \
  --publish 3306:3306 \
  --publish 33060:33060 \
  mysql-server