ARG BUILDPLATFORM="amd64"
FROM --platform=${BUILDPLATFORM} mysql:8.0-debian

LABEL version="1.0"

ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8"

COPY --chown=mysql:mysql "mysql_config.cnf.tpl" "/opt/"
COPY "store_credentials.exp" "/opt/"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

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
      "curl=7.88.1-10+deb12u7" \
      "expect=5.45.4-2+b1" \
      "gosu=1.14-1+b10" \
  && \
  curl \
    --location \
    --output \
      envsubst \
        "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64" \
  && \
  chmod \
    555 \
      "envsubst" \
  && \
  mkdir \
    "/etc/mysql/ssl" \
  && \
  apt-get \
    clean \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"

ENTRYPOINT [ "/bin/bash", "-c", " \
  chmod \
    444 \
      /var/run/mysqld/mysql_root_password \
  && \
  chown \
    --recursive \
      mysql:mysql \
    /etc/mysql/ssl \
    /etc/mysql/conf.d \
    /var/run/mysqld \
  && \
  gosu \
    mysql \
      ./envsubst \
        -no-unset \
        -no-empty \
          < /opt/mysql_config.cnf.tpl \
          > /etc/mysql/conf.d/mysql_config.cnf \
  && \
  exec \
    gosu \
      mysql \
        docker-entrypoint.sh \
        mysqld \
  & \
  sleep \
    ${HEALTHCHECK_START_PERIOD} \
  && \
  chmod \
    400 \
      /var/run/mysqld/mysql_root_password \
  && \
  chown \
    --recursive \
      root:root \
    /var/run/mysqld \
  && \
  tail \
    --follow \
      /dev/null \
        -- \
  " \
]
