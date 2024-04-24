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
    --file tests/setup/Dockerfile \
    --tag node \
    .

  # ssh-keygen -t rsa -b 2048 -f id_rsa -N ""
  # ssh-add id_rsa
  # echo "StrictHostKeyChecking no" | tee --append "/etc/ssh/ssh_config"

  for ((node = 0; node < nodes; node++)); do
    docker run \
      --detach \
      --privileged \
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
    
    echo "172.18.0.$((2 + $node)) node-${node}" >> /etc/hosts
  done
}

# set_mysql_mgmt_nodes() {
#   local hostname="${1}"

#   docker exec \
#     --user root \
#     "${hostname}" \
#       sh -c "/app/services/mysql-server/run.sh"
# }

# set_mysql_server_nodes() {
#   local hostname="${1}"

#   docker exec \
#     --user root \
#     "${hostname}" \
#       sh -c "/app/services/mysql-mgmt/run.sh"
# }

set_network
set_nodes 4
# set_mysql_mgmt_nodes
# set_mysql_server_nodes

scp -r services/mysql-server "root@172.18.0.3:/opt"
ssh root@172.18.0.3 "service docker start"
ssh root@172.18.0.3 "/opt/mysql-server/run.sh"

scp -r services/mysql-server "root@172.18.0.4:/opt"
ssh root@172.18.0.4 "service docker start"
ssh root@172.18.0.4 "/opt/mysql-server/run.sh"

scp -r services/mysql-server "root@172.18.0.5:/opt"
ssh root@172.18.0.5 "service docker start"
ssh root@172.18.0.5 "/opt/mysql-server/run.sh"

scp -r services/mysql-mgmt "root@172.18.0.2:/opt"
ssh root@172.18.0.2 "service docker start"
ssh root@172.18.0.2 "/opt/mysql-mgmt/run.sh"


# ssh root@wiktor-ctl.mgr.suse.de 'cd /root/spacewalk/testsuite && cucumber features/core/srv_first_settings.eature:25'
