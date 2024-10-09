ARG BUILDPLATFORM="amd64"
FROM --platform=${BUILDPLATFORM} ubuntu:22.04

LABEL version="1.0"

ARG MYSQL_SHELL_VERSION="mysql-shell-8.3.0-linux-glibc2.28-x86-64bit" \
    MYSQL_SHELL_MD5_CHECKSUM="c71280416014b9340b34b90160f42e23" \
    MYSQL_ROUTER_VERSION="mysql-router-8.3.0-linux-glibc2.28-x86_64" \
    MYSQL_ROUTER_MD5_CHECKSUM="6ea1c55a258d20fc51a4c383a1e7433e"

COPY --chown=superset:superset . "/opt"

ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    DEBIAN_FRONTEND="noninteractive" \
    PATH="${PATH}:/opt/${MYSQL_SHELL_VERSION}/bin:/opt/${MYSQL_ROUTER_VERSION}/bin"

WORKDIR "/opt"

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
      "gpg=2.2.27-3ubuntu2.1" \
      "ifmetric=0.3-5" \
      "keepalived=1:2.2.4-0.2build1" \
      "libkeyutils1=1.6.1-2ubuntu3" \
      "mysql-client=8.0.39-0ubuntu0.22.04.1" \
      "sudo=1.9.9-1ubuntu2.4" \
      "wget=1.21.2-2ubuntu1.1" \
      "xz-utils=5.2.5-2ubuntu1" \
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
  gpg \
    --import \
      "/opt/dev_mysql_signature.asc" \
  && \
  wget \
    --quiet \
      "https://github.com/a8m/envsubst/releases/download/v1.2.0/envsubst-Linux-x86_64" \
      "https://dev.mysql.com/get/Downloads/MySQL-Shell/${MYSQL_SHELL_VERSION}.tar.gz" \
      "https://dev.mysql.com/get/Downloads/MySQL-Router/${MYSQL_ROUTER_VERSION}.tar.xz" \
  && \
  echo "${MYSQL_SHELL_MD5_CHECKSUM}  ${MYSQL_SHELL_VERSION}.tar.gz" \
    | md5sum \
      --check \
        - \
  && \
  echo "${MYSQL_ROUTER_MD5_CHECKSUM}  ${MYSQL_ROUTER_VERSION}.tar.xz" \
    | md5sum \
      --check \
        - \
  && \
  wget \
    --quiet \
    --output-document \
      "${MYSQL_SHELL_VERSION}.tar.gz.asc" \
        "https://downloads.mysql.com/archives/gpg/?file=${MYSQL_SHELL_VERSION}.tar.gz&p=43" \
  && \
  gpg \
    --verify \
      "${MYSQL_SHELL_VERSION}.tar.gz.asc" \
  && \
  wget \
    --quiet \
    --output-document \
      "${MYSQL_ROUTER_VERSION}.tar.xz.asc" \
        "https://downloads.mysql.com/archives/gpg/?file=${MYSQL_ROUTER_VERSION}.tar.xz&p=41" \
  && \
  gpg \
    --verify \
      "${MYSQL_ROUTER_VERSION}.tar.xz.asc" \
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
  echo \
    "superset ALL=(ALL) NOPASSWD: /usr/sbin/keepalived" \
      >> \
        "/etc/sudoers.d/keepalived" \
  && \
  apt-get \
    clean \
  && \
  rm \
    --recursive \
    --force \
      "${MYSQL_SHELL_VERSION}.tar.gz" \
      "${MYSQL_ROUTER_VERSION}.tar.xz" \
      "/var/lib/apt/lists/*"
