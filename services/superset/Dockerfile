FROM apache/superset

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

ENTRYPOINT [ "bash", "-c", "celery --app=superset.tasks.celery_app:app worker --pool=prefork -O fair -c 4 & /usr/bin/run-server.sh" ]
