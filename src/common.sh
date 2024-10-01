#!/bin/bash

array_to_string_converter() {
  local string_result=""
  for node in "${@}"; do
    string_result+="${node} "
  done
  echo "${string_result}"
}

initialize_nodes() {
  # export MYSQL_TEST_LOGIN_FILE="${_path_to_root_catalog}/services/mysql-mgmt/.mylogin.cnf"
  # ./${_path_to_root_catalog}/store_credentials.exp ${mysql_nodes[@]} ${_path_to_root_catalog}
  
  primary_node=$(echo ${mysql_nodes[@]} | awk '{print $1}')
  mysql_root_password=$(ssh superset@${primary_node} "openssl rand -base64 16")
  ca_key=$(ssh superset@${primary_node} "openssl genpkey -algorithm RSA -out /dev/stdout")
  ca_certificate=$(ssh superset@${primary_node} "openssl req -new -x509 -key <(printf '%s\n' '${ca_key}') -days 365 -subj "/CN=Superset-Cluster" -out /dev/stdout")
  # superset_cluster_key=$(ssh superset@${primary_node} "openssl genpkey -algorithm RSA -out /dev/stdout")
  # superset_cluster_csr=$(ssh superset@${primary_node} "openssl req -new -key <(printf '%s\n' '${superset_cluster_key}') -out /dev/stdout -subj '/CN=${virtual_ip_address}'")
  # superset_cluster_cert=$(ssh superset@${primary_node} "openssl x509 -in <(printf '%s\n' '${superset_cluster_csr}') -CA <(printf '%s\n' '${ca_certificate}') -CAkey <(printf '%s\n' '${ca_key}') -CAcreateserial -out /dev/stdout -req -days 365")

  for mysql_node in "${mysql_nodes[@]}"; do
    ssh superset@${mysql_node} "mkdir /opt/superset-cluster"
    scp -r "${_path_to_root_catalog}/services/mysql-server" "superset@${mysql_node}:/opt/superset-cluster"
    ssh superset@${mysql_node} "echo ${mysql_root_password} > /opt/superset-cluster/mysql-server/mysql_root_password"
    ssh superset@${mysql_node} "printf '%s\n' '${ca_key}' > /opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem"
    ssh superset@${mysql_node} "printf '%s\n' '${ca_certificate}' > /opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem"
    ssh superset@${mysql_node} "/opt/superset-cluster/mysql-server/init.sh"
  done
  
  encoded_mysql_login_file=$(ssh superset@${primary_node} " \
    docker exec --user root --env MYSQL_TEST_LOGIN_FILE=/var/run/mysqld/.mylogin.cnf \
    mysql sh -c '/opt/store_credentials.exp ${mysql_nodes[@]} && \
    cat /var/run/mysqld/.mylogin.cnf | base64'")

  STATE="MASTER"
  PRIORITY="100"
  for mgmt_node in "${mgmt_nodes[@]}"; do
    ssh superset@${mgmt_node} "mkdir /opt/superset-cluster"
    scp -r ${_path_to_root_catalog}/services/mysql-mgmt "superset@${mgmt_node}:/opt/superset-cluster"
    ssh superset@${mgmt_node} "printf '%s\n' '${ca_key}' > /opt/superset-cluster/mysql-mgmt/superset_cluster_ca_key.pem"
    ssh superset@${mgmt_node} "printf '%s\n' '${ca_certificate}' > /opt/superset-cluster/mysql-mgmt/superset_cluster_ca_certificate.pem"
    scp -r ${_path_to_root_catalog}/services/superset "superset@${mgmt_node}:/opt/superset-cluster"
    ssh superset@${mgmt_node} "printf '%s\n' '${ca_key}' > /opt/superset-cluster/superset/superset_cluster_ca_key.pem"
    ssh superset@${mgmt_node} "printf '%s\n' '${ca_certificate}' > /opt/superset-cluster/superset/superset_cluster_ca_certificate.pem"
    ssh superset@${mgmt_node} "docker swarm init --advertise-addr ${virtual_ip_address}"
    ssh superset@${mgmt_node} "docker network create --driver overlay --attachable superset-network"
    ssh superset@${mgmt_node} "echo cluster > /opt/superset-cluster/mysql-mgmt/mysql_superset_password"
    ssh superset@${mgmt_node} "printf '%s\n' '${encoded_mysql_login_file}' | base64 --decode  > /opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
    ssh superset@${mgmt_node} "chmod 600 /opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
    ssh superset@${mgmt_node} "export STATE=${STATE} && export PRIORITY=${PRIORITY} && /opt/superset-cluster/mysql-mgmt/init.sh ${virtual_ip_address} ${virtual_ip_address_mask} ${virtual_network_interface} ${VIRTUAL_NETWORK} $(array_to_string_converter ${mysql_nodes[@]})"
    ssh superset@${mgmt_node} "docker login ghcr.io -u szachovy -p ..."
    ssh superset@${mgmt_node} "docker pull ghcr.io/szachovy/superset-cluster-service:latest"
    ssh superset@${mgmt_node} "echo $(openssl rand -base64 42) | docker secret create superset_secret_key -"
    ssh superset@${mgmt_node} "echo cluster | docker secret create mysql_superset_password -"
    # ssh superset@${mgmt_node} "printf '%s\n' '${superset_cluster_key}' > /opt/superset-cluster/superset/superset_cluster_key.pem"
    # ssh superset@${mgmt_node} "printf '%s\n' '${superset_cluster_cert}' > /opt/superset-cluster/superset/superset_cluster_certificate.pem"
    ssh superset@${mgmt_node} "/opt/superset-cluster/superset/init.sh ${virtual_ip_address}"
    STATE="BACKUP"
    PRIORITY="90"
  done
}
