FROM debian

ARG MYSQL_SHELL_VERSION=mysql-shell-8.3.0-linux-glibc2.28-x86-64bit
ARG MYSQL_ROUTER_VERSION=mysql-router-8.3.0-linux-glibc2.28-x86_64

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=$PATH:/opt/${MYSQL_SHELL_VERSION}/bin:/opt/${MYSQL_ROUTER_VERSION}/bin

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
      xz-utils

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

ENTRYPOINT [ "sleep", "infinity" ]
