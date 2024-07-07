FROM mysql:8.0-debian

ARG SERVER_ID
ARG MYSQL_DATABASE
ARG MYSQL_USER
ARG MYSQL_PASSWORD

ENV SERVER_ID="${SERVER_ID}"
# ENV MYSQL_DATABASE="${MYSQL_DATABASE}"
# ENV MYSQL_USER=${MYSQL_USER}

COPY . /opt

WORKDIR /opt

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      curl \
      expect \
  && \
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

RUN useradd --create-home --system ${MYSQL_USER}
RUN chown --recursive ${MYSQL_USER} /var/lib/mysql

# USER ${MYSQL_USER}

CMD [ "/opt/entrypoint.sh" ]
