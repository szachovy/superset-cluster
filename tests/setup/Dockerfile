FROM ubuntu:22.04

USER root

ENV PYTHONPATH /opt/superset-cluster:${PYTHONPATH}

RUN \
  apt \
    update \
  && \
  apt \ 
    install \
      --yes \
      ca-certificates=20230311ubuntu0.22.04.1 \
      curl=7.81.0-1ubuntu1.16 \
  && \
  install \
    --mode \
      0755 \
    --directory \
      /etc/apt/keyrings \
  && \
  curl \
    --location \
      https://download.docker.com/linux/ubuntu/gpg \
    --output \
      /etc/apt/keyrings/docker.asc \
  && \
  chmod \
    644 \
      /etc/apt/keyrings/docker.asc \
  && \
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
    https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null \
  && \
  mkdir \
    "/root/.ssh" \
  && \
  chmod \
    700 \
      "/root/.ssh" \
  && \
  mkdir \
    "/opt/superset-cluster" \
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

COPY --chown=root "id_rsa.pub" "/root/.ssh/authorized_keys"

ENTRYPOINT [ "bash", "-c", "service ssh start \
  && echo 'nameserver 8.8.8.8' >> /etc/resolv.conf \
  && echo 'nameserver 8.8.4.4' >> /etc/resolv.conf \
  && service docker start \
  && tail --follow /dev/null" ]
