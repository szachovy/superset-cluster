FROM mysql:8.0-debian

ARG SERVER_ID
ENV SERVER_ID="${SERVER_ID}"

COPY \
  "mysql_root_password.txt" \
  "mysql_config.cnf.tpl" \
    "/opt/"

COPY \
  "mysql_server_${SERVER_ID}_certificate.pem" \
  "mysql_server_${SERVER_ID}_key.pem" \
  "superset_cluster_ca_certificate.pem" \
    "/etc/mysql/ssl/"

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      curl \
  && \
  curl \
    --location \
    --output \
      envsubst \
        "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64" \
  && \
  chmod \
    500 \
      envsubst \
  && \
    ./envsubst \
      -no-unset \
      -no-empty \
        < "/opt/mysql_config.cnf.tpl" > "/etc/mysql/conf.d/mysql_config.cnf" \
  && \
  chown \
    --recursive \
      mysql:mysql \
        "/opt" \
        "/etc/mysql/ssl" \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"

USER mysql
