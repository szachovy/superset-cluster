FROM ubuntu:22.04

COPY . "/opt"

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      libkeyutils1=1.6.1-2ubuntu3 \
      wget=1.21.2-2ubuntu1.1 \
      xz-utils=5.2.5-2ubuntu1 \
      keepalived=1:2.2.4-0.2build1 \
      mysql-client=8.0.37-0ubuntu0.22.04.3 \
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
  chown \
    --recursive \
      superset:superset \
        "/opt/initcontainer" \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"

USER superset

ARG MYSQL_SHELL_VERSION="mysql-shell-8.3.0-linux-glibc2.28-x86-64bit"
ARG MYSQL_ROUTER_VERSION="mysql-router-8.3.0-linux-glibc2.28-x86_64"

ENV DEBIAN_FRONTEND="noninteractive"
ENV PATH="${PATH}:/home/superset/${MYSQL_SHELL_VERSION}/bin:/home/superset/${MYSQL_ROUTER_VERSION}/bin"
# ENV MYSQL_TEST_LOGIN_FILE="/home/superset/.mylogin.cnf"

WORKDIR "/home/superset"

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
      "/home/superset/envsubst-Linux-x86_64" \
  && \
  rm \
    "${MYSQL_SHELL_VERSION}.tar.gz" \
    "${MYSQL_ROUTER_VERSION}.tar.xz"

ENTRYPOINT [ "sleep", "infinity" ]
