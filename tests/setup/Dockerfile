ARG BUILDPLATFORM="amd64"
FROM --platform=${BUILDPLATFORM} ubuntu:22.04

LABEL version="1.0"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

RUN \
  set \
    -eux \
  && \
  apt-get \
    update \
  && \
  apt-get \ 
    install \
      --yes \
      "ca-certificates=20240203~22.04.1" \
      "curl=7.81.0-1ubuntu1.18" \
  && \
  install \
    --mode \
      0755 \
    --directory \
      "/etc/apt/keyrings" \
  && \
  curl \
    --location \
      "https://download.docker.com/linux/ubuntu/gpg" \
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
  chown \
    superset:superset \
      "/opt" \
      "/home/superset/.ssh" \
  && \
  apt-get \
    update \
  && \
  apt-get \
    install \
      --yes \
      "containerd.io=1.6.31-1" \
      "docker-buildx-plugin=0.14.0-1~ubuntu.22.04~jammy" \
      "docker-ce=5:26.1.0-1~ubuntu.22.04~jammy" \
      "docker-ce-cli=5:26.1.0-1~ubuntu.22.04~jammy" \
      "openssh-server=1:8.9p1-3ubuntu0.10" \
  && \
  apt-get \
    clean \
  && \
  rm \
    --recursive \
    --force \
      "/var/lib/apt/lists/*"
    
COPY --chown=superset:superset "id_rsa.pub" "/home/superset/.ssh/authorized_keys"

USER superset

ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONPATH="/opt/superset-cluster:${PYTHONPATH}"

ENTRYPOINT ["/bin/bash", "-c", "tail --follow /dev/null --"]
