#!/bin/bash

set_network() {
  docker network create \
    --subnet=172.18.0.0/16 \
    --gateway=172.18.0.1 \
    mysql-network
}

set_nodes() {
  local nodes="${1}"
  
  docker build \
    --tag node \
    ./tests/setup

  # ssh-keygen -t rsa -b 2048 -f id_rsa -N ""
  # sleep 5
  # ssh-add id_rsa
  # echo "StrictHostKeyChecking no" | sudo tee --append "/etc/ssh/ssh_config"

  for ((node = 0; node < nodes; node++)); do
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
      --volume $(pwd)/id_rsa.pub:/root/.ssh/id_rsa.pub \
      node
    fi
    docker run \
      --detach \
      --privileged \
      --ulimit nofile=65535 \
      --name "node-${node}" \
      --hostname "node-${node}" \
      --publish "$((2222+${node})):22" \
      --ip 172.18.0.$((2 + $node)) \
      --network mysql-network \
      --volume $(pwd)/id_rsa.pub:/root/.ssh/id_rsa.pub \
      node

    docker exec \
      --user root \
      "node-${node}" \
        sh -c "cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys"
  done
}

# set_mysql_mgmt_nodes() {
#   local hostname="${1}"

#   docker exec \
#     --user root \
#     "${hostname}" \
#       sh -c "/app/services/mysql-server/init.sh"
# }

# set_mysql_server_nodes() {
#   local hostname="${1}"

#   docker exec \
#     --user root \
#     "${hostname}" \
#       sh -c "/app/services/mysql-mgmt/init.sh"
# }

set_network
set_nodes 5
# set_mysql_mgmt_nodes
# set_mysql_server_nodes

scp -r services/mysql-server "root@172.18.0.3:/opt"
# ssh root@172.18.0.3 "service docker start"
ssh root@172.18.0.3 "/opt/mysql-server/init.sh"

scp -r services/mysql-server "root@172.18.0.4:/opt"
# ssh root@172.18.0.4 "service docker start"
ssh root@172.18.0.4 "/opt/mysql-server/init.sh"

scp -r services/mysql-server "root@172.18.0.5:/opt"
# ssh root@172.18.0.5 "service docker start"
ssh root@172.18.0.5 "/opt/mysql-server/init.sh"

scp -r services/mysql-mgmt "root@172.18.0.2:/opt"
# ssh root@172.18.0.2 "service docker start"
ssh root@172.18.0.2 "/opt/mysql-mgmt/init.sh 172.18.0.3 172.18.0.4 172.18.0.5"

for ((n = 0; n < nodes; n++)); do
  if [ $n != $node ]; then
    docker exec \
      --user root \
      "node-${node}" \
      sh -c "echo '172.18.0.$((2 + n))  node-${n}' >> /etc/hosts"
  fi
done

docker restart node-1
sleep 5
ssh root@172.18.0.3 "service docker restart"

docker restart node-2
sleep 5
ssh root@172.18.0.4 "service docker restart"

docker restart node-3
sleep 5
ssh root@172.18.0.5 "service docker restart"

ssh root@172.18.0.2 "/opt/mysql-mgmt/clusterize.sh 172.18.0.3 172.18.0.4 172.18.0.5"

set_superset() {
  scp -r services/redis "root@172.18.0.6:/opt"
  scp -r services/superset "root@172.18.0.6:/opt"
  ssh root@172.18.0.6 "docker network create superset-network"
  ssh root@172.18.0.6 "/opt/redis/init.sh"
  ssh root@172.18.0.6 "/opt/superset/init.sh"
}
set_superset
# add etc/hosts
# 172.18.0.2      node-0
# 172.18.0.3      node-1
# 172.18.0.4      node-2
# 172.18.0.5      node-3
