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
      net-tools

USER superset

COPY --chown=superset superset_config.py /app/
ENV SUPERSET_CONFIG_PATH /app/superset_config.py

RUN \
  pip \
    install \
      mysqlclient \
      flower \
      redis \
      mysql-connector-python

ENTRYPOINT ["bash", "-c", \
      "superset fab create-admin --username admin --firstname admin --lastname admin --email admin@admin.com --password admin && \
       superset db upgrade && \
       superset load_examples && \
       superset init && \
       /usr/bin/run-server.sh"]

