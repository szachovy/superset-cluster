FROM apache/superset

USER root

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
        expect \
  && \
  apt \
    clean

USER superset

COPY --chown=superset "superset_config.py" "prev" "/app/"
ENV SUPERSET_CONFIG_PATH="/app/superset_config.py"
ENV SECRET_KEY="$(openssl rand -base64 42)"

RUN \
  pip \
    install \
      redis \
      mysql-connector-python

ENTRYPOINT [ "sh", "-c", \
  "./prev && \
  superset re-encrypt-secrets \
  && celery --app superset.tasks.celery_app:app worker --pool prefork --concurrency 4 -O fair --detach \
  && /usr/bin/run-server.sh" \
]
