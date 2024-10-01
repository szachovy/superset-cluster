FROM mysql:8.0-debian

COPY --chown=mysql "mysql_config.cnf.tpl" "/opt/"
COPY "store_credentials.exp" "/opt/"

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      curl \
      expect \
      gosu \
  && \
  curl \
    --location \
    --output \
      envsubst \
        "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64" \
  && \
  chmod \
    555 \
      envsubst \
  && \
  mkdir \
    "/etc/mysql/ssl" \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"

ENTRYPOINT sh -c " \
  chmod 444 /var/run/mysqld/mysql_root_password && \
  chown --recursive mysql:mysql /etc/mysql/ssl /etc/mysql/conf.d/ && \
  gosu mysql ./envsubst -no-unset -no-empty < /opt/mysql_config.cnf.tpl > /etc/mysql/conf.d/mysql_config.cnf && \
  exec gosu mysql docker-entrypoint.sh mysqld & \
  sleep ${HEALTHCHECK_START_PERIOD} && \
  chmod 400 /var/run/mysqld/mysql_root_password && \
  chown --recursive root:root /var/run/mysqld && \
  tail -f /dev/null"
