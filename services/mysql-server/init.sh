#!/bin/bash

HEALTHCHECK_START_PERIOD=20
HEALTHCHECK_INTERVAL=5
HEALTHCHECK_RETRIES=3
SERVER_ID="$((RANDOM % 4294967295 + 1))"

openssl \
  genpkey \
    -algorithm RSA \
    -out "/opt/superset-cluster/mysql-server/mysql_server_${SERVER_ID}_key.pem"

openssl \
  req \
    -new \
    -key "/opt/superset-cluster/mysql-server/mysql_server_${SERVER_ID}_key.pem" \
    -out "/opt/superset-cluster/mysql-server/mysql_server_${SERVER_ID}_certificate_signing_request.pem" \
    -subj "/CN=Superset-Cluster-MySQL-Server-${SERVER_ID}"

openssl \
  x509 \
    -in "/opt/superset-cluster/mysql-server/mysql_server_${SERVER_ID}_certificate_signing_request.pem" \
    -CA "/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem" \
    -CAkey "/opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem" \
    -CAcreateserial \
    -out "/opt/superset-cluster/mysql-server/mysql_server_${SERVER_ID}_certificate.pem" \
    -req \
    -days 365

docker build \
  --build-arg SERVER_ID="${SERVER_ID}" \
  --tag mysql-server \
  /opt/superset-cluster/mysql-server

docker run \
  --detach \
  --name mysql \
  --hostname "${HOSTNAME}" \
  --network host \
  --cap-add SYS_NICE \
  --security-opt seccomp=/opt/superset-cluster/mysql-server/seccomp.json \
  --health-cmd "mysqladmin ping" \
  --health-start-period "${HEALTHCHECK_START_PERIOD}s" \
  --health-interval "${HEALTHCHECK_INTERVAL}s" \
  --health-retries ${HEALTHCHECK_RETRIES} \
  --health-timeout "10s" \
  --env MYSQL_INITDB_SKIP_TZINFO="true" \
  --env MYSQL_ROOT_PASSWORD_FILE="/opt/mysql_root_password.txt" \
  mysql-server

sleep ${HEALTHCHECK_START_PERIOD}

for _ in $(seq 1 ${HEALTHCHECK_RETRIES}); do
  if [ "$(docker inspect --format '{{json .State.Health.Status}}' "mysql")" = '"healthy"' ]; then
    docker exec --user=root mysql /bin/bash -c "
      chmod 400 /opt/mysql_root_password.txt \
      && chown --recursive root:root /opt /var/run/mysqld /etc/mysql/ssl"
  else
    sleep ${HEALTHCHECK_INTERVAL}
  fi
done
