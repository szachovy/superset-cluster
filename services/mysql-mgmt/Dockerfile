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
      keepalived \
      mysql-client \
      expect

RUN \
  wget \
    https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64 \
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
      ${MYSQL_ROUTER_VERSION}.tar.xz \
  && \
  mv \
    envsubst-Linux-x86_64 \
      /usr/bin/envsubst \
  && \
  chmod \
    744 \
      /usr/bin/envsubst

ENTRYPOINT [ "sleep", "infinity" ]
# ENTRYPOINT [ \
#   "/bin/bash", \
#     "/opt/entrypoint.sh", \
#       "true", \
#       "172.18.0.10", \
#       "eth0", \
#       "mysql", \
#       "172.18.0.3", \
#       "172.18.0.4", \
#       "172.18.0.5" \
# ]
# /bin/bash /opt/entrypoint.sh true 172.18.0.10 eth0 mysql 172.18.0.3 172.18.0.4 172.18.0.5
