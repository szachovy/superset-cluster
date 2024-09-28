#!/bin/bash

# docker build --tag superset-cluster-mysql-server:latest .
# docker tag superset-cluster-mysql-server:latest ghcr.io/szachovy/superset-cluster-mysql-server:latest
# docker push ghcr.io/szachovy/superset-cluster-mysql-server:latest

HEALTHCHECK_START_PERIOD=90

openssl \
  genpkey \
    -algorithm RSA \
    -out "/opt/superset-cluster/mysql-server/mysql_server_key.pem"

openssl \
  req \
    -new \
    -key "/opt/superset-cluster/mysql-server/mysql_server_key.pem" \
    -out "/opt/superset-cluster/mysql-server/mysql_server_certificate_signing_request.pem" \
    -subj "/CN=Superset-Cluster-MySQL-Server-${HOSTNAME}"

openssl \
  x509 \
    -in "/opt/superset-cluster/mysql-server/mysql_server_certificate_signing_request.pem" \
    -CA "/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem" \
    -CAkey "/opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem" \
    -CAcreateserial \
    -out "/opt/superset-cluster/mysql-server/mysql_server_certificate.pem" \
    -req \
    -days 365

# temporary
docker build \
  --tag mysql-server \
  /opt/superset-cluster/mysql-server

docker run \
  --detach \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --restart "always" \
  --network host \
  --cap-add SYS_NICE \
  --security-opt seccomp=/opt/superset-cluster/mysql-server/seccomp.json \
  --env MYSQL_INITDB_SKIP_TZINFO="true" \
  --env MYSQL_ROOT_PASSWORD_FILE="/var/run/mysqld/mysql_root_password" \
  --env SERVER_ID="$((RANDOM % 4294967295 + 1))" \
  --env HEALTHCHECK_START_PERIOD=${HEALTHCHECK_START_PERIOD} \
  --health-cmd "mysqladmin ping" \
  --health-start-period "${HEALTHCHECK_START_PERIOD}s" \
  --health-interval "5s" \
  --health-retries 3 \
  --health-timeout "10s" \
  --volume "/opt/superset-cluster/mysql-server/mysql_root_password:/var/run/mysqld/mysql_root_password" \
  --volume "/opt/superset-cluster/mysql-server/mysql_server_certificate.pem:/etc/mysql/ssl/mysql_server_certificate.pem" \
  --volume "/opt/superset-cluster/mysql-server/mysql_server_key.pem:/etc/mysql/ssl/mysql_server_key.pem" \
  --volume "/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem:/etc/mysql/ssl/superset_cluster_ca_certificate.pem" \
  mysql-server
  #ghcr.io/szachovy/superset-cluster-mysql-server:latest
  
  #mysql-server

# sleep ${HEALTHCHECK_START_PERIOD}

# for _ in $(seq 1 ${HEALTHCHECK_RETRIES}); do
#   if [ "$(docker inspect --format '{{json .State.Health.Status}}' "mysql")" = '"healthy"' ]; then
#     docker exec --user=root mysql /bin/bash -c "
#       chmod 400 /opt/mysql_root_password.txt \
#       && chown --recursive root:root /opt /var/run/mysqld /etc/mysql/ssl"
#   else
#     sleep ${HEALTHCHECK_INTERVAL}
#   fi
# done

# export mysql_root_password=$(openssl rand -base64 16)
# echo $mysql_root_password | docker secret create superset_database_root -

# docker service create \
#   --with-registry-auth \
#   --detach \
#   --secret superset_database_root \
#   --name mysql-server \
#   --publish 3306:3306 \
#   --hostname "${HOSTNAME}" \
#   --cap-add SYS_NICE \
#   --replicas 1 \
#   --health-cmd "mysqladmin ping" \
#   --health-start-period "15s" \
#   --health-interval "5s" \
#   --health-retries 3 \
#   --health-timeout "10s" \
#   --env MYSQL_INITDB_SKIP_TZINFO="true" \
#   --env MYSQL_ROOT_PASSWORD_FILE="/run/secrets/superset_database_root" \
#   --env SERVER_ID="$((RANDOM % 4294967295 + 1))" \
#   --mount type=bind,source=/opt/superset-cluster/mysql-server/mysql_server_certificate.pem,target=/etc/mysql/ssl/mysql_server_certificate.pem \
#   --mount type=bind,source=/opt/superset-cluster/mysql-server/mysql_server_key.pem,target=/etc/mysql/ssl/mysql_server_key.pem \
#   --mount type=bind,source=/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem,target=/etc/mysql/ssl/superset_cluster_ca_certificate.pem \
#   ghcr.io/szachovy/superset-cluster-mysql-server:latest


# docker create \
#   --rm \
#   --name mysql \
#   --hostname "${HOSTNAME}" \
#   --network host \
#   --cap-add SYS_NICE \
#   --security-opt seccomp=/opt/superset-cluster/mysql-server/seccomp.json \
#   --env MYSQL_INITDB_SKIP_TZINFO="true" \
#   --env MYSQL_ROOT_PASSWORD_FILE="/var/run/mysqld/mysql_root_password.txt" \
#   --env SERVER_ID="$((RANDOM % 4294967295 + 1))" \
#   --mount "type=bind,source=/opt/superset-cluster/mysql-server/mysql_server_certificate.pem,destination=/etc/mysql/ssl/mysql_server_certificate.pem" \
#   --mount "type=bind,source=/opt/superset-cluster/mysql-server/mysql_server_key.pem,destination=/etc/mysql/ssl/mysql_server_key.pem" \
#   --mount "type=bind,source=/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem,destination=/etc/mysql/ssl/superset_cluster_ca_certificate.pem" \
#   mysql-server

# docker cp /opt/superset-cluster/mysql-server/mysql_root_password.txt mysql:/var/run/mysqld/mysql_root_password.txt
