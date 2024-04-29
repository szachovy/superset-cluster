#!/bin/bash

nodes="${1}"

set_network() {
  docker network create \
    --subnet=172.18.0.0/16 \
    --gateway=172.18.0.1 \
    mysql-network
}

set_nodes() {
  docker build \
    --tag node \
    ./setup

  ssh-keygen -t rsa -b 2048 -f id_rsa -N ""
  sleep 5
  ssh-add id_rsa
  # echo "StrictHostKeyChecking no" | sudo tee --append "/etc/ssh/ssh_config"

  for ((node = 0; node < ${nodes}; node++)); do
    if [ $node == 4 ]; then
      docker run \
      --detach \
      --privileged \
      --ulimit nofile=65535 \
      --name "node-${node}" \
      --hostname "node-${node}" \
      --publish "$((2222+${node})):22" \
      --publish "8088:8088" \
      --ip 172.18.0.$((2 + $node)) \
      --network mysql-network \
      node
    else
      docker run \
        --detach \
        --privileged \
        --ulimit nofile=65535 \
        --name "node-${node}" \
        --hostname "node-${node}" \
        --publish "$((2222+${node})):22" \
        --publish "$((2378+${node})):2377" \
        --publish "$((7947+${node})):7946" \
        --publish "$((4790+${node})):4789" \
        --ip 172.18.0.$((2 + $node)) \
        --network mysql-network \
        node
    fi

    docker cp id_rsa.pub "node-${node}":/root/.ssh

    docker exec \
      "node-${node}" \
        sh -c "cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys"

    for ((n = 0; n < ${nodes}; n++)); do
      if [ $n != $node ]; then
        docker exec \
          --user root \
          "node-${node}" \
            sh -c "echo '172.18.0.$((2 + n))  node-${n}' >> /etc/hosts"
      fi
    done
  done
}

set_network
set_nodes
