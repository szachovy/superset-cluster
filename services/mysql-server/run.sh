MYSQL_ROOT_PASSWORD=mysql

docker build \
  --build-arg MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
  --build-arg MYSQL_DATABASE=superset \
  --tag mysql-server \
  .

docker run \
  --detach \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --publish 3306:3306 \
  mysql-server