FROM apache/superset

USER root

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      iproute2 \
      net-tools \
      procps \
      curl \
      wget \
      net-tools \
      iputils-ping \
      telnet \
      dnsutils \
      tcpdump \
      strace \
      nano \
      && \
  rm -rf /var/lib/apt/lists/*

USER superset

COPY --chown=superset src/superset_config.py /app/
ENV SUPERSET_CONFIG_PATH /app/superset_config.py

RUN \
  pip \
    install \
      mysqlclient \
      flower \
      redis \
      mysql-connector-python

ENTRYPOINT [ "bash", "-c", "celery --app=superset.tasks.celery_app:app worker --pool=prefork -O fair -c 4 & /usr/bin/run-server.sh" ]
# ENTRYPOINT [ "bash", "-c", "sleep infinity" ]
# ENTRYPOINT ["bash", "-c", \
#       "superset fab create-admin --username admin --firstname admin --lastname admin --email admin@admin.com --password admin && \
#        superset db upgrade && \
#        superset load_examples && \
#        superset init && \
#        sleep infinity"]

      #  && \
      #  /usr/bin/run-server.sh

