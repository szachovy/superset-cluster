#!/bin/bash

array_to_string_converter() {
  local string_result=""
  for node in "${@}"; do
    string_result+="${node} "
  done
  echo "${string_result}"
}

initialize_nodes() {
  export MYSQL_TEST_LOGIN_FILE="${_path_to_root_catalog}/services/mysql-mgmt/.mylogin.cnf"
  ./${_path_to_root_catalog}/store_credentials.exp ${mysql_nodes[@]} ${_path_to_root_catalog}

  mysql_root_password=$(openssl rand -base64 16)
  for mysql_node in "${mysql_nodes[@]}"; do
    ssh superset@${mysql_node} "mkdir /opt/superset-cluster"
    scp -r "${_path_to_root_catalog}/services/mysql-server" "superset@${mysql_node}:/opt/superset-cluster"
    ssh superset@${mysql_node} "echo ${mysql_root_password} > /opt/superset-cluster/mysql-server/mysql_root_password"
    ssh superset@${mysql_node} "/opt/superset-cluster/mysql-server/init.sh"
  done

  # VIRTUAL_NETWORK=$(python3 -c "import interfaces; print(interfaces.virtual_network('${virtual_ip_address}','${virtual_ip_address_mask}'))")
  # ssh superset@${mysql_nodes[0]} " \
  #   docker exec --user root --env MYSQL_TEST_LOGIN_FILE='/var/run/mysqld/.mylogin.cnf' \
  #   mysql /opt/store_credentials.exp ${mysql_nodes[@]} \
  #   chmod 400 /var/run/mysqld/.mylogin.cnf"

  # encoded_mysql_login_file=$(ssh superset@node-2 " \
  #   docker exec --user root --env MYSQL_TEST_LOGIN_FILE=/var/run/mysqld/.mylogin.cnf \
  #   mysql sh -c '/opt/store_credentials.exp node-2 node-3 node-4 && \
  #   cat /var/run/mysqld/.mylogin.cnf | base64'")

  # encoded_mysql_login_file=$(ssh superset@${mysql_nodes[0]} " \
  #   docker exec --user root --env MYSQL_TEST_LOGIN_FILE=/var/run/mysqld/.mylogin.cnf \
  #   mysql /opt/store_credentials.exp ${mysql_nodes[@]} \
  #   cat /var/run/mysqld/.mylogin.cnf | base64")

  primary_node=$(echo ${mysql_nodes[@]} | awk '{print $1}')
  encoded_mysql_login_file=$(ssh superset@${primary_node} " \
    docker exec --user root --env MYSQL_TEST_LOGIN_FILE=/var/run/mysqld/.mylogin.cnf \
    mysql sh -c '/opt/store_credentials.exp ${mysql_nodes[@]} && \
    cat /var/run/mysqld/.mylogin.cnf | base64'")

  for mgmt_node in "${mgmt_nodes[@]}"; do
    ssh superset@${mgmt_node} "mkdir /opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/mysql-mgmt "superset@${mgmt_node}:/opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/superset "superset@${mgmt_node}:/opt/superset-cluster"
# ssh superset@${mgmt_node} "cat <<EOF > /opt/superset-cluster/mysql-mgmt/.mylogin.cnf 
# echo ${encoded_mysql_login_file} 
# EOF"
# AAAAABcaDgAbGgsHGhQSChsLAxAMChgKEAAAABMui5urAXCHUrvorhFZcU4QAAAAoXpe/D4uXjpU
# QwrBAXLJ9xAAAAA8smkapJhCCpEsibWOSDv2IAAAALFD5dIARAJANpAXQhFIrKoYurpe/Ik/Omt2
# rVK3Ze+vEAAAAFrP3lEW7By67y6xStcq75AQAAAAoXpe/D4uXjpUQwrBAXLJ9xAAAAA8smkapJhC
# CpEsibWOSDv2IAAAAKkwn98vwhjAI+S7Q8wLMyAYurpe/Ik/Omt2rVK3Ze+vEAAAAPv+9d+7EglA
# ipG6BPbfGr4QAAAAoXpe/D4uXjpUQwrBAXLJ9xAAAAA8smkapJhCCpEsibWOSDv2IAAAAPzTkvCY
# QOfn8pQac+07fuIYurpe/Ik/Omt2rVK3Ze+v
    if [ "${mgmt_node}" = "${mgmt_nodes[0]}" ]; then
      ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address}"
      ssh superset@${mgmt_node} "docker network create --driver overlay --attachable superset-network"
      ssh superset@${mgmt_node} "echo cluster > /opt/superset-cluster/mysql-mgmt/mysql_superset_password"
      ssh superset@${mgmt_node} "printf '%s\n' '${encoded_mysql_login_file}' | base64 --decode  > /opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
      ssh superset@${mgmt_node} "chmod 600 /opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
      ssh superset@${mgmt_node} "echo 'export STATE=MASTER' >> ~/.bashrc"
      ssh superset@${mgmt_node} "echo 'export PRIORITY=100' >> ~/.bashrc"
      ssh superset@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh ${virtual_ip_address} ${virtual_ip_address_mask} ${virtual_network_interface} ${VIRTUAL_NETWORK} $(array_to_string_converter ${mysql_nodes[@]})"
      ssh superset@${mgmt_node} "docker login ghcr.io -u szachovy -p ..."
      ssh superset@${mgmt_node} "docker pull ghcr.io/szachovy/superset-cluster:latest"
      ssh superset@${mgmt_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
      ssh superset@${mgmt_node} "echo cluster | docker secret create mysql_superset_password -"
      ssh superset@${mgmt_node} "/opt/superset-cluster/superset/init.sh ${virtual_ip_address} || true"
    else
      exit 0
      ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address}"
      ssh superset@${mgmt_node} "docker network create --driver overlay --attachable superset-network"
      ssh superset@${mgmt_node} "echo cluster > /opt/superset-cluster/mysql-mgmt/mysql_superset_password"
      ssh superset@${mgmt_node} "printf '%s\n' '${encoded_mysql_login_file}' | base64 --decode  > /opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
      ssh superset@${mgmt_node} "chmod 600 /opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
      ssh superset@${mgmt_node} "echo 'export STATE=BACKUP' >> ~/.bashrc && source ~/.bashrc"
      ssh superset@${mgmt_node} "echo 'export PRIORITY=90' >> ~/.bashrc && source ~/.bashrc"
      ssh superset@${mgmt_node} "/opt/superset-cluster/mysql-mgmt/init.sh ${virtual_ip_address} ${virtual_ip_address_mask} ${virtual_network_interface} ${VIRTUAL_NETWORK} $(array_to_string_converter ${mysql_nodes[@]})"
      ssh superset@${mgmt_node} "docker login ghcr.io -u szachovy -p ..."
      ssh superset@${mgmt_node} "docker pull ghcr.io/szachovy/superset-cluster:latest"
      ssh superset@${mgmt_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
      ssh superset@${mgmt_node} "echo cluster | docker secret create mysql_superset_password -"
      ssh superset@${mgmt_node} "/opt/superset-cluster/superset/init.sh ${virtual_ip_address} || true"
    fi
  done
}
