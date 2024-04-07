docker network create --subnet=172.18.0.0/16 --gateway=172.18.0.1 mysql-network

docker run -d --name mysql-primary \
    -e MYSQL_ROOT_PASSWORD=mysql \
    -e MYSQL_DATABASE=superset \
    -v ./services/mysql-server/mysql-config.cnf:/etc/mysql/conf.d/mysql-config.cnf \
    --network mysql-network \
    mysql:latest

docker run -d --name mysql-secondary-1 \
    -e MYSQL_ROOT_PASSWORD=mysql \
    -e MYSQL_DATABASE=superset \
    -v ./services/mysql-server/mysql-config.cnf:/etc/mysql/conf.d/mysql-config.cnf \
    --network mysql-network \
    mysql:latest

docker run -d --name mysql-secondary-2 \
    -e MYSQL_ROOT_PASSWORD=mysql \
    -e MYSQL_DATABASE=superset \
    -v ./services/mysql-server/mysql-config.cnf:/etc/mysql/conf.d/mysql-config.cnf \
    --network mysql-network \
    mysql:latest