FROM apache/superset:4.0.2

USER root

COPY --chown=superset "." "/app/"

RUN apt-get update && \
    apt-get install -y nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER superset
ENV SUPERSET_CONFIG_PATH="/app/superset_config.py"
RUN chown --recursive superset:superset /var/lib/nginx /var/log/nginx /app
COPY --chown=superset nginx.conf /etc/nginx/nginx.conf
COPY --chown=superset superset_cluster_certificate.pem /etc/ssl/certs/superset_cluster_certificate.pem
COPY --chown=superset superset_cluster_key.pem /etc/ssl/certs/superset_cluster_key.pem

CMD nginx & /usr/bin/run-server.sh