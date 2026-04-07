ARG BUILDPLATFORM="amd64"
FROM --platform=${BUILDPLATFORM} ubuntu:22.04

LABEL version="1.0"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

# hadolint ignore=DL3008,SC2086
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
      --no-install-recommends \
      "ca-certificates" \
      "curl" \
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
      --no-install-recommends \
      "containerd.io" \
      "docker-buildx-plugin" \
      "docker-ce" \
      "docker-ce-cli" \
      "openssh-server" \
      "python3" \
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
