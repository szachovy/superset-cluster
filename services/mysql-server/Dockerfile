FROM mysql:8.0-debian

ARG SERVER_ID
ENV SERVER_ID="${SERVER_ID}"

COPY . "/opt"

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      curl \
      expect \
  && \
  curl \
    --location \
    --output \
      envsubst \
        "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64" \
  && \
  chmod \
    700 \
      envsubst \
  && \
    ./envsubst < "/opt/mysql_config.cnf.tpl" > "/etc/mysql/conf.d/mysql_config.cnf" \
  && \
  groupadd \
    --system \
      "superset" \
  && \
  useradd \
    --system \
    --gid \
      "superset" \
    --create-home \
    --home-dir \
      "/home/superset" \
    --shell \
      "/bin/bash" \
    superset \
  && \
  mv \
    "/opt/entrypoint.sh" \
    "/opt/store_credentials" \
    "/home/superset" \
  && \
  if [ -f "/opt/.mylogin.cnf" ]; then \
    mv "/opt/.mylogin.cnf" "/home/superset/"; \
  fi \
  && \
  chown \
    --recursive \
      superset:superset \
        "/var/lib/mysql" \
        "/var/run/mysqld" \
        "/home/superset" \
  && \
  chmod \
    500 \
      "/home/superset/entrypoint.sh" \
  && \
  chmod \
    500 \
      "/home/superset/store_credentials" \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"

USER superset

WORKDIR "/home/superset"

ENV MYSQL_TEST_LOGIN_FILE="/home/superset/.mylogin.cnf"

ENTRYPOINT [ "/home/superset/entrypoint.sh" ]
