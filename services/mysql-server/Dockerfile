FROM mysql:8.3

ARG SERVER_ID
ARG MYSQL_ROOT_PASSWORD
ARG MYSQL_DATABASE

ENV SERVER_ID="${SERVER_ID}"
ENV MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}"
ENV MYSQL_DATABASE="${MYSQL_DATABASE}"

COPY . /opt

WORKDIR /opt

RUN \
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
    ./envsubst < "/opt/mysql_config.cnf.tpl" > "/etc/mysql/conf.d/mysql_config.cnf"
