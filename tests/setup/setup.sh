#!/bin/bash

nodes=5

set_network() {
  docker network create \
    --subnet=172.18.0.0/16 \
    --gateway=172.18.0.1 \
    mysql-network
}

set_ssh_keys() {
  # ssh-keygen -t rsa -b 2048 -f id_rsa -N ""
  chmod 600 id_rsa.pub
  ssh-add id_rsa
  # echo "StrictHostKeyChecking no" | sudo tee --append "/etc/ssh/ssh_config"
}

set_hostname_resolution() {
  local current_node="${1}"
  local node=0
  while [ ${node} -lt ${nodes} ]; do
    if [ ${node} != ${current_node} ]; then
      docker exec \
        --user "root" \
        "node-${current_node}" \
          sh -c "echo '172.18.0.$((2 + ${node}))  node-${node}' >> /etc/hosts"
    fi
    let "node+=1"
  done
}

set_nodes() {
  docker build \
    --tag "node" \
    ./setup

  for ((node = 0; node < ${nodes}; node++)); do
    docker run \
      --detach \
      --privileged \
      --ulimit "nofile=65535" \
      --name "node-${node}" \
      --hostname "node-${node}" \
      --ip "172.18.0.$((2 + ${node}))" \
      --publish "$((8088 + ${node})):8088" \
      --network "mysql-network" \
      node

    docker exec \
      --interactive \
      --user "root" \
      "node-${node}" \
        sh -c "cat > /root/.ssh/authorized_keys" < id_rsa.pub

    set_hostname_resolution "${node}"
  done
}

set_network
set_ssh_keys
set_nodes
