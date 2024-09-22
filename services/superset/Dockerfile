FROM apache/superset:4.0.2

USER root

COPY --chown=superset "." "/app/"

RUN \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
        expect \
  && \
  chmod \
    500 \
      entrypoint.sh \
      set-database-uri.exp \
  && \
  chmod \
    400 \
      mysql_connect.py \
      superset_config.py \
  && \
  apt \
    clean

USER superset

ENV SUPERSET_CONFIG_PATH="/app/superset_config.py"

RUN \
  pip \
    install \
      redis \
      mysql-connector-python

ENTRYPOINT [ "/app/entrypoint.sh" ]
