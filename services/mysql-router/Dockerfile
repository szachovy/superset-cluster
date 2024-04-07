FROM alpine AS builder

ARG MYSQL_SHELL_VERSION=mysql-shell-8.3.0-linux-glibc2.28-x86-64bit

WORKDIR /opt

RUN \
  apk \
    --no-cache \
      add \
        wget \
  && \
  wget \
    https://dev.mysql.com/get/Downloads/MySQL-Shell/${MYSQL_SHELL_VERSION}.tar.gz \
  && \
  tar \
    --extract \
    --file \
      ${MYSQL_SHELL_VERSION}.tar.gz

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

FROM container-registry.oracle.com/mysql/community-router
USER root
RUN mkdir --parents /var/lib/mysqlrouter
RUN chown -R mysqlrouter /var/lib/mysqlrouter
USER mysqlrouter
COPY --from=builder /opt/${MYSQL_SHELL_VERSION} /opt/
ARG MYSQL_SHELL_VERSION=mysql-shell-8.3.0-linux-glibc2.28-x86-64bit
ENV PATH=$PATH:/opt/${MYSQL_SHELL_VERSION}/bin





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
#         mysql-shell