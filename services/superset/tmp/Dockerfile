FROM apache/superset:4.0.2

USER root

RUN apt-get update && \
    apt-get install -y nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY superset_cluster_certificate.pem /etc/ssl/certs/superset_cluster_certificate.pem
COPY superset_cluster_key.pem /etc/ssl/certs/superset_cluster_key.pem

CMD service nginx start && /usr/bin/run-server.sh