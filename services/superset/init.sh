#!/bin/bash

# docker build --tag superset-cluster-service:latest .
# docker tag superset-cluster-service:latest ghcr.io/szachovy/superset-cluster-service:latest
# docker push ghcr.io/szachovy/superset-cluster-service:latest

openssl \
  genpkey \
    -algorithm RSA \
    -out "superset_cluster_key.pem"

openssl \
  req \
    -new \
    -key "superset_cluster_key.pem" \
    -out "superset_cluster_certificate_signing_request.pem" \
    -subj "/CN=Superset-Cluster-MySQL-Server-${HOSTNAME}"

openssl \
  x509 \
    -in "superset_cluster_certificate_signing_request.pem" \
    -CA "superset_cluster_ca_certificate.pem" \
    -CAkey "superset_cluster_ca_key.pem" \
    -CAcreateserial \
    -out "superset_cluster_certificate.pem" \
    -req \
    -days 365

docker service create \
  --with-registry-auth \
  --detach \
  --name superset \
  --secret superset_secret_key \
  --secret mysql_superset_password \
  --publish 443:443 \
  --network superset-network \
  --replicas 1 \
  --health-start-period=60s \
  --health-interval=30s \
  --health-retries=10 \
  --health-timeout=5s \
  --env VIRTUAL_IP_ADDRESS="172.18.0.10" \
  ghcr.io/szachovy/superset-cluster-service:latest

# --publish 8088:8088 \