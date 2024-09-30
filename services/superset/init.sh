#!/bin/bash

# docker build --tag superset-cluster-service:latest .
# docker tag superset-cluster-service:latest ghcr.io/szachovy/superset-cluster-service:latest
# docker push ghcr.io/szachovy/superset-cluster-service:latest

VIRTUAL_IP_ADDRESS="${1}"

openssl \
  genpkey \
    -algorithm RSA \
    -out "/opt/superset-cluster/superset/superset_cluster_key.pem"

openssl \
  req \
    -new \
    -key "/opt/superset-cluster/superset/superset_cluster_key.pem" \
    -out "/opt/superset-cluster/superset/superset_cluster_certificate_signing_request.pem" \
    -subj "/CN=${VIRTUAL_IP_ADDRESS}"

openssl \
  x509 \
    -in "/opt/superset-cluster/superset/superset_cluster_certificate_signing_request.pem" \
    -CA "/opt/superset-cluster/superset/superset_cluster_ca_certificate.pem" \
    -CAkey "/opt/superset-cluster/superset/superset_cluster_ca_key.pem" \
    -CAcreateserial \
    -out "/opt/superset-cluster/superset/superset_cluster_certificate.pem" \
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
  --health-retries=20 \
  --health-timeout=5s \
  --env VIRTUAL_IP_ADDRESS="${VIRTUAL_IP_ADDRESS}" \
  --mount type=bind,source=/opt/superset-cluster/superset/superset_cluster_certificate.pem,target=/etc/ssl/certs/superset_cluster_certificate.pem \
  --mount type=bind,source=/opt/superset-cluster/superset/superset_cluster_key.pem,target=/etc/ssl/certs/superset_cluster_key.pem \
  ghcr.io/szachovy/superset-cluster-service:latest

sleep 60

for attempt in {1..20}; do
  if [ $(docker service ls --filter "name=superset" --format "{{.Replicas}}") == "1/1" ]; then
    exit 0
  else
    echo "Waiting for the service to become healthy... (Attempt $attempt/20)"
    sleep 30
  fi
done

exit 1
