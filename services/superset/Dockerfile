FROM apache/superset

USER superset

ARG VIRTUAL_IP_ADDRESS
ARG ENVIRONMENT

COPY --chown=superset "superset_config.py" "/app/"

ENV SUPERSET_CONFIG_PATH="/app/superset_config.py"
ENV VIRTUAL_IP_ADDRESS="${VIRTUAL_IP_ADDRESS}"
ENV ENVIRONMENT="${ENVIRONMENT}"

RUN \
  pip \
    install \
      redis \
      mysql-connector-python \
  && \
  superset \
    fab \
      create-admin \
        --username \
          "superset" \
        --firstname \
          "superset" \
        --lastname \
          "superset" \
        --email \
          "superset@cluster.com" \
        --password \
          "cluster" \
  && \
  superset \
    db \
      upgrade \
  && \
  superset load_examples \
  &&  \
  superset \
    init

ENTRYPOINT [ "sh", "-c", \
  "celery --app superset.tasks.celery_app:app worker --pool prefork --concurrency 4 -O fair --detach && /usr/bin/run-server.sh" \
]

# if [ "${ENVIRONMENT}" == "testing" ]; then \
#     superset load_examples; \
#   fi \