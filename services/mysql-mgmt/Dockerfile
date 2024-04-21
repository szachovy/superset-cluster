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

# RUN \
#   wget \
#     https://dev.mysql.com/get/${MYSQL_CONFIG_VERSION}.deb \
#   && \
#   dpkg \
#     --install \
#     ${MYSQL_CONFIG_VERSION}.deb \
#   && \
#   apt \
#     update \
#   && \
#   apt \
#     install \
#       --yes \
#       mysql-shell \
#       mysql-router \
#   && \ 
#   rm \
#     ${MYSQL_CONFIG_VERSION}.deb \
#   && \
#   apt \
#     clean \
#   && \
#   rm \
#     --recursive \
#     --force \
#     /var/lib/apt/lists/*

# RUN \
#   wget \
#     https://dev.mysql.com/get/mysql-apt-config_0.8.29-1_all.deb \
#   && \
#   dpkg \
#     --install \
#       mysql-apt-config_0.8.29-1_all.deb \
#   apt \
#     update \
#   && \
#   apt \
#     install \
#       --yes \
#         mysql-shell \
#         mysql-router

# FROM alpine

# RUN apk add --no-cache wget debconf dpkg \
#   && wget https://dev.mysql.com/get/mysql-apt-config_0.8.29-1_all.deb \
#   && dpkg-deb --install mysql-apt-config_0.8.29-1_all.deb \
#   && apk add --no-cache mysql-shell mysql-router \
#   && rm mysql-apt-config_0.8.29-1_all.deb

# FROM alpine

# ARG MYSQL_SHELL_VERSION=mysql-shell-8.3.0-linux-glibc2.28-x86-64bit
# ENV PATH=$PATH:/opt/${MYSQL_SHELL_VERSION}/bin

# WORKDIR /opt
# RUN \
#   apk \
#     --no-cache \
#       add \
#         wget \
#   && \
#   wget \
#     https://dev.mysql.com/get/Downloads/MySQL-Shell/${MYSQL_SHELL_VERSION}.tar.gz \
#     https://dev.mysql.com/get/Downloads/MySQL-8.3/mysql-8.3.0-linux-glibc2.28-x86_64.tar.xz \
#   && \
#   tar \
#     --extract \
#     --file \
#       ${MYSQL_SHELL_VERSION}.tar.gz

# RUN \
#   curl \
#     --location \
#       https://dev.mysql.com/get/Downloads/MySQL-Shell/$MYSQL_SHELL_VERSION.tar.gz \
#         > $MYSQL_SHELL_VERSION.tar.gz \
#   && \
#   tar \
#     --extract \
#     --file \
#       ${MYSQL_SHELL_VERSION}.tar.gz

# FROM container-registry.oracle.com/mysql/community-router
# USER root
# RUN mkdir --parents /var/lib/mysqlrouter
# RUN chown -R mysqlrouter /var/lib/mysqlrouter
# USER mysqlrouter
# COPY --from=builder /opt/${MYSQL_SHELL_VERSION} /opt/
# ARG MYSQL_SHELL_VERSION=mysql-shell-8.3.0-linux-glibc2.28-x86-64bit
# ENV PATH=$PATH:/opt/${MYSQL_SHELL_VERSION}/bin





# RUN \
#   apt \
#     update \
#   && \
#   apt \
#     install \
#       --yes \
#         wget \
#         lsb-release \
#         gnupg

# RUN \
  # wget \
  #   https://dev.mysql.com/get/Downloads/MySQL-Shell/${MYSQL_SHELL_VERSION}.tar.gz \