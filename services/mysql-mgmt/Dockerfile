FROM ubuntu:22.04

ARG MYSQL_SHELL_VERSION=mysql-shell-8.3.0-linux-glibc2.28-x86-64bit
ARG MYSQL_ROUTER_VERSION=mysql-router-8.3.0-linux-glibc2.28-x86_64

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=$PATH:/opt/${MYSQL_SHELL_VERSION}/bin:/opt/${MYSQL_ROUTER_VERSION}/bin

COPY . /opt

WORKDIR /opt

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      libkeyutils1 \
      wget \
      xz-utils \
      sysvinit-utils \
      keepalived

RUN \
  wget \
    https://dev.mysql.com/get/Downloads/MySQL-Shell/${MYSQL_SHELL_VERSION}.tar.gz \
    https://dev.mysql.com/get/Downloads/MySQL-Router/${MYSQL_ROUTER_VERSION}.tar.xz \
  && \
  tar \
    --extract \
    --file \
      ${MYSQL_SHELL_VERSION}.tar.gz \
  && \
  tar \
    --xz \
    --extract \
    --file \
      ${MYSQL_ROUTER_VERSION}.tar.xz


# ENTRYPOINT [ "sleep", "infinity" ]
# RUN echo "/opt/entrypoint.sh ${IS_PRIMARY_MGMT_NODE} ${VIRTUAL_IP_ADDRESS} ${NETWORK_INTERFACE} ${SUPERSET_USER_PASSWORD} ${MYSQL_NODES}"
# ENTRYPOINT [ "/opt/entrypoint.sh" ]
ENTRYPOINT keepalived --use-file "/opt/initcontainer/keepalived.conf" && mysqlrouter --config "/opt/initcontainer/mysql_router/mysqlrouter.conf"

# /bin/bash /opt/entrypoint.sh true 172.18.0.10 eth0 mysql node-1 node-2 node-3
