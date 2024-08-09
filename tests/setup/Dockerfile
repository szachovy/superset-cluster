FROM ubuntu:22.04

USER root

RUN \
  apt \
    update \
  && \
  apt \ 
    install \
      --yes \
      ca-certificates \
      curl \
      nano \
  && \
  install \
    --mode \
      0755 \
    --directory \
      "/etc/apt/keyrings" \
  && \
  curl \
    --location \
      https://download.docker.com/linux/ubuntu/gpg \
    --output \
      "/etc/apt/keyrings/docker.asc" \
  && \
  chmod \
    644 \
      "/etc/apt/keyrings/docker.asc" \
  && \
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
    https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
      tee "/etc/apt/sources.list.d/docker.list" > /dev/null \
  && \
  groupadd \
    --system \
      "superset" \
  && \
  useradd \
    --system \
    --gid \
      "superset" \
    --create-home \
    --home-dir \
      "/home/superset" \
    --shell \
      "/bin/bash" \
    superset \
  && \
  mkdir \
    --mode \
      700 \
      "/home/superset/.ssh" \
  && \
  chmod \
    700 \
      "/home/superset/.ssh" \
  && \
  mkdir \
    "/opt/superset-cluster" \
  && \
  chown \
    superset:superset \
      "/opt/superset-cluster" \
      "/home/superset/.ssh" \
  && \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      containerd.io=1.6.31-1 \
      docker-buildx-plugin=0.14.0-1~ubuntu.22.04~jammy \
      docker-ce=5:26.1.0-1~ubuntu.22.04~jammy \
      docker-ce-cli=5:26.1.0-1~ubuntu.22.04~jammy \
      openssh-server=1:8.9p1-3ubuntu0.10 \
  && \
  apt \
    clean

COPY --chown=superset:superset "id_rsa.pub" "/home/superset/.ssh/authorized_keys"

USER superset

ENV PYTHONPATH="/opt/superset-cluster:${PYTHONPATH}"

ENTRYPOINT ["/bin/bash", "-c", "tail --follow /dev/null"]
