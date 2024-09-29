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

# docker build . -t superset-nginx
# docker run --name superset-nginx -p 443:443 superset-nginx