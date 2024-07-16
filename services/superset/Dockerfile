FROM apache/superset

USER superset

ARG PRELOAD_EXAMPLES=false

COPY --chown=superset superset_config.py /app/
ENV SUPERSET_CONFIG_PATH /app/superset_config.py

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
          superset \
        --firstname \
          superset \
        --lastname \
          superset \
        --email \
          superset@cluster.com \
        --password \
          cluster \
  && \
    superset \
      db \
        upgrade \
  && \
    if ${PRELOAD_EXAMPLES}; then \
      superset load_examples; \
    fi \
  &&  \
    superset \
      init

ENTRYPOINT $(pwd)/services/superset/entrypoint.sh
