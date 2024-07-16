FROM mysql:8.0-debian

ARG SERVER_ID
ENV SERVER_ID="${SERVER_ID}"

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
        https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64 \
  && \
  chmod \
    744 \
      envsubst \
  && \
    ./envsubst < "/opt/mysql_config.cnf.tpl" > "/etc/mysql/conf.d/mysql_config.cnf" \
  && \
  groupadd \
    --system \
      superset \
  && \
  useradd \
    --system \
    --gid \
      superset \
    --create-home \
    --home-dir \
      /home/superset \
    --shell \
      /bin/bash \
    superset \
  && \
  chown \
    --recursive \
      superset:superset \
        /var/run/mysqld \
  && \
  rm \
    --recursive \
    --force \
      /var/lib/apt/lists/*

USER superset

COPY . "${HOME}"
WORKDIR "${HOME}"

CMD [ "${HOME}/entrypoint.sh" ]
