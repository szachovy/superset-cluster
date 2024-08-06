FROM ubuntu:22.04

COPY . "/opt"

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
      keepalived \
      mysql-client \
      sudo \
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
  mkdir \
    "/opt/initcontainer" \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"

ARG MYSQL_SHELL_VERSION="mysql-shell-8.3.0-linux-glibc2.28-x86-64bit"
ARG MYSQL_ROUTER_VERSION="mysql-router-8.3.0-linux-glibc2.28-x86_64"

ENV DEBIAN_FRONTEND="noninteractive"
ENV PATH="${PATH}:/opt/${MYSQL_SHELL_VERSION}/bin:/opt/${MYSQL_ROUTER_VERSION}/bin"
ENV MYSQL_TEST_LOGIN_FILE="/opt/.mylogin.cnf"

WORKDIR "/opt"

RUN \
  wget \
    --quiet \
      "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64" \
      "https://dev.mysql.com/get/Downloads/MySQL-Shell/${MYSQL_SHELL_VERSION}.tar.gz" \
      "https://dev.mysql.com/get/Downloads/MySQL-Router/${MYSQL_ROUTER_VERSION}.tar.xz" \
  && \
  tar \
    --extract \
    --file \
      "${MYSQL_SHELL_VERSION}.tar.gz" \
  && \
  tar \
    --xz \
    --extract \
    --file \
      "${MYSQL_ROUTER_VERSION}.tar.xz" \
  && \
  chmod \
    744 \
      "/opt/envsubst-Linux-x86_64" \
  && \
  rm \
    "${MYSQL_SHELL_VERSION}.tar.gz" \
    "${MYSQL_ROUTER_VERSION}.tar.xz" \
  && \
  echo \
    "superset ALL=(ALL) NOPASSWD: /usr/sbin/keepalived" \
      >> \
        "/etc/sudoers.d/keepalived"
