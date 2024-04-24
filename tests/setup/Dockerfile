FROM ubuntu:22.04

USER root

RUN \
  apt \
    update \
  && \
  apt \ 
    install \
      --yes \
      openssh-server \
      ca-certificates \
      curl \
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
    a+r \
      /etc/apt/keyrings/docker.asc \
  && \
  echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null \
  && \
  apt \
    update \
  && \
  apt \
    install \
      --yes \
      docker-ce \
      docker-ce-cli \
      containerd.io \
      docker-buildx-plugin \
  # && \
  # usermod \
  #   --append \
  #   --groups \
  #     docker \
  #       ${USER} \
  && \
  apt \
    clean

ENTRYPOINT ["sh", "-c", "service ssh start && tail -f /dev/null"]
