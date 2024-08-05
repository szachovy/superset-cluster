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

COPY --chown=superset "." "/app/"
ENV SUPERSET_CONFIG_PATH="/app/superset_config.py"

RUN \
  pip \
    install \
      redis \
      mysql-connector-python

ENTRYPOINT [ "/app/entrypoint.sh" ]
