ARG BUILDPLATFORM="amd64"
FROM --platform=${BUILDPLATFORM} apache/superset:4.0.2

LABEL version="1.0"

COPY --chown=superset:superset "." "/app/"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER superset

ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    SUPERSET_CONFIG_PATH="/app/superset_config.py"

RUN \
  pip \
    install \
      --no-cache-dir \
      "redis==4.5.4" \
      "mysql-connector-python==9.0.0"

USER root

RUN \
  set \
    -eux \
  && \
  apt-get \
    update \
  && \
  apt-get \
    install \
      --yes \
      "expect=5.45.4-2+b1" \
      "gosu=1.14-1+b10" \
      "nginx=1.22.1-9" \
  && \
  chown \
    --recursive \
      superset:superset \
    "/var/lib/nginx" \
    "/var/log/nginx" \
  && \
  apt-get \
    clean \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"

COPY --chown=superset:superset "nginx.conf" "/etc/nginx/nginx.conf"

ENTRYPOINT [ "/bin/bash", "-c", " \
  chown \
    --recursive \
      superset:superset \
    /etc/ssl/certs \
    /app \
  && \
  gosu \
    superset \
      nginx \
  & \
  exec \
    gosu \
      superset \
        /app/entrypoint.sh \
  && \
  chown \
    --recursive \
      root:root \
    /app \
  " \
]
