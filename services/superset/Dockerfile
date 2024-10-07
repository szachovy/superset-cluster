FROM apache/superset:4.0.2

USER root

COPY --chown=superset "." "/app/"

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
        expect \
        gosu \
        nginx \
  && \
  chmod \
    500 \
      entrypoint.sh \
      set_database_uri.exp \
  && \
  chmod \
    400 \
      mysql_connect.py \
      superset_config.py \
  && \
  chown \
    --recursive \
      superset:superset \
        /var/lib/nginx \
        /var/log/nginx \
        /app \
  && \
  apt \
    clean \
  && \
  rm \
    --recursive \
    --force \
      /var/lib/apt/lists/*

USER superset

COPY --chown=superset "nginx.conf" "/etc/nginx/nginx.conf"

ENV SUPERSET_CONFIG_PATH="/app/superset_config.py"

RUN \
  pip \
    install \
      redis \
      mysql-connector-python

USER root

ENTRYPOINT sh -c " \
  chown --recursive superset:superset /etc/ssl/certs && \
  gosu superset nginx & exec gosu superset /app/entrypoint.sh"
