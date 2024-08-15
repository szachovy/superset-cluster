#!/bin/bash

export IS_PRIMARY_MGMT_NODE="${1}"
export VIRTUAL_NETWORK_INTERFACE="${4}"
export PRIMARY_MYSQL_NODE="${6}"
export SECONDARY_FIRST_MYSQL_NODE="${7}"
export SECONDARY_SECOND_MYSQL_NODE="${8}"
export HEALTHCHECK_START_PERIOD=20

cat << EOF > /opt/superset-cluster/mysql-mgmt/.env-initcontainer
VIRTUAL_IP_ADDRESS="${2}"
VIRTUAL_IP_ADDRESS_MASK="${3}"
VIRTUAL_NETWORK_INTERFACE="${4}"
VIRTUAL_NETWORK="${5}"
MYSQL_TEST_LOGIN_FILE="/opt/.mylogin.cnf"
EOF

# cat << EOF > /opt/superset-cluster/mysql-mgmt/.env-maincontainer
# VIRTUAL_NETWORK_INTERFACE="${4}"
# PRIMARY_MYSQL_NODE="${6}"
# HEALTHCHECK_START_PERIOD=20
# EOF

# exit 0
# export VIRTUAL_IP_ADDRESS="172.18.0.8"
# export VIRTUAL_IP_ADDRESS_MASK="255.255.0.0"
# export VIRTUAL_NETWORK="172.18.0.0/16"

# export IS_PRIMARY_MGMT_NODE="true"
export VIRTUAL_NETWORK_INTERFACE="eth0"
export PRIMARY_MYSQL_NODE="node-1"
export HEALTHCHECK_START_PERIOD=20
# export SECONDARY_FIRST_MYSQL_NODE="node-2"
# export SECONDARY_SECOND_MYSQL_NODE="node-3"
# export MYSQL_TEST_LOGIN_FILE="/opt/superset-cluster/mysql-mgmt/.mylogin.cnf"

# openssl \
#   genpkey \
#     -algorithm RSA \
#     -out "/opt/superset-cluster/mysql-mgmt/mysql_router_${HOSTNAME}_key.pem"

# openssl \
#   req \
#     -new \
#     -key "/opt/superset-cluster/mysql-mgmt/mysql_router_${HOSTNAME}_key.pem" \
#     -out "/opt/superset-cluster/mysql-mgmt/mysql_router_${HOSTNAME}_certificate_signing_request.pem" \
#     -subj "/CN=Superset-Cluster-MySQL-Router-${HOSTNAME}"

# openssl \
#   x509 \
#     -in "/opt/superset-cluster/mysql-mgmt/mysql_router_${HOSTNAME}_certificate_signing_request.pem" \
#     -CA "/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_certificate.pem" \
#     -CAkey "/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_key.pem" \
#     -CAcreateserial \
#     -out "/opt/superset-cluster/mysql-mgmt/mysql_router_${HOSTNAME}_certificate.pem" \
#     -req \
#     -days 365

docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up initcontainer \
&& \
docker compose \
  --file /opt/superset-cluster/mysql-mgmt/docker-compose.yml up maincontainer \
  --detach

# export VIRTUAL_NETWORK_INTERFACE='eth0'
# export PRIMARY_MYSQL_NODE='172.18.0.3'

# ip monitor dev ${VIRTUAL_NETWORK_INTERFACE} > /opt/default/ifstatus &
# sudo keepalived --use-file '/opt/default/keepalived.conf' \
# && \
# timeout ${HEALTHCHECK_START_PERIOD} bash -c "watch -g -n 1 'stat /opt/default/ifstatus'" \
# && \
# if [ ! -d "/opt/default/mysql_router/" ]; then \
#   mysqlrouter --user "superset" --bootstrap "superset:cluster@${PRIMARY_MYSQL_NODE}:3306" --directory "/opt/default/mysql_router" --conf-use-sockets; \
# fi \
# && \
# mysqlrouter --config "/opt/default/mysql_router/mysqlrouter.conf"

# timeout ${HEALTHCHECK_START_PERIOD} bash -c "/opt/default/ifstatus | while read -r line; do echo hi; rm /opt/default/ifstatus && kill -9 $MONITOR_PID; break; done"

# ( ip monitor dev ${VIRTUAL_NETWORK_INTERFACE} ) &
# MONITOR_PID=$!
# sudo keepalived --use-file '/opt/default/keepalived.conf'
# timeout ${HEALTHCHECK_START_PERIOD} bash -c "strace -p $MONITOR_PID -e write=1 | while read -r line; do kill -9 $MONITOR_PID; break; done"

# tail -f /proc/$MONITOR_PID/fd/1
# timeout ${HEALTHCHECK_START_PERIOD} bash -c "ip monitor link dev ${VIRTUAL_NETWORK_INTERFACE} | while read -r line; do sudo keepalived --use-file '/opt/default/keepalived.conf'; break; done"


# mysqlsh --login-path=mysqlrouter-user --sql --ssl-mode=REQUIRED --host=127.0.0.1 --port=6446
# SHOW STATUS LIKE 'Ssl_cipher';

# root@node-0:/opt/initcontainer/mysql_router# cat mysqlrouter.conf 
# # File automatically generated during MySQL Router bootstrap
# [DEFAULT]
# user=superset
# logging_folder=/opt/initcontainer/mysql_router/log
# runtime_folder=/opt/initcontainer/mysql_router/run
# data_folder=/opt/initcontainer/mysql_router/data
# keyring_path=/opt/initcontainer/mysql_router/data/keyring
# master_key_path=/opt/initcontainer/mysql_router/mysqlrouter.key
# connect_timeout=5
# read_timeout=30
# dynamic_state=/opt/initcontainer/mysql_router/data/state.json
# client_ssl_cert=/opt/initcontainer/mysql_router/data/router-cert.pem
# client_ssl_key=/opt/initcontainer/mysql_router/data/router-key.pem
# client_ssl_mode=PREFERRED
# server_ssl_mode=PREFERRED
# server_ssl_verify=DISABLED
# unknown_config_option=error
# max_idle_server_connections=64
# router_require_enforce=1

# [logger]
# level=INFO

# [metadata_cache:bootstrap]
# cluster_type=gr
# router_id=1
# user=mysql_router1_7x6pzt80si56
# metadata_cluster=superset
# ttl=0.5
# auth_cache_ttl=-1
# auth_cache_refresh_interval=2
# use_gr_notifications=0

# [routing:bootstrap_rw]
# bind_address=0.0.0.0
# bind_port=6446
# socket=/opt/initcontainer/mysql_router/mysql.sock
# destinations=metadata-cache://superset/?role=PRIMARY
# routing_strategy=first-available
# protocol=classic

# [routing:bootstrap_ro]
# bind_address=0.0.0.0
# bind_port=6447
# socket=/opt/initcontainer/mysql_router/mysqlro.sock
# destinations=metadata-cache://superset/?role=SECONDARY
# routing_strategy=round-robin-with-fallback
# protocol=classic

# [routing:bootstrap_rw_split]
# bind_address=0.0.0.0
# bind_port=6450
# socket=/opt/initcontainer/mysql_router/mysqlsplit.sock
# destinations=metadata-cache://superset/?role=PRIMARY_AND_SECONDARY
# routing_strategy=round-robin
# protocol=classic
# connection_sharing=1
# client_ssl_mode=PREFERRED
# server_ssl_mode=PREFERRED
# access_mode=auto

# [routing:bootstrap_x_rw]
# bind_address=0.0.0.0
# bind_port=6448
# socket=/opt/initcontainer/mysql_router/mysqlx.sock
# destinations=metadata-cache://superset/?role=PRIMARY
# routing_strategy=first-available
# protocol=x
# router_require_enforce=0
# client_ssl_ca=
# server_ssl_key=
# server_ssl_cert=

# [routing:bootstrap_x_ro]
# bind_address=0.0.0.0
# bind_port=6449
# socket=/opt/initcontainer/mysql_router/mysqlxro.sock
# destinations=metadata-cache://superset/?role=SECONDARY
# routing_strategy=round-robin-with-fallback
# protocol=x
# router_require_enforce=0
# client_ssl_ca=
# server_ssl_key=
# server_ssl_cert=

# [http_server]
# port=8443
# ssl=1
# ssl_cert=/opt/initcontainer/mysql_router/data/router-cert.pem
# ssl_key=/opt/initcontainer/mysql_router/data/router-key.pem

# [http_auth_realm:default_auth_realm]
# backend=default_auth_backend
# method=basic
# name=default_realm

# [rest_router]
# require_realm=default_auth_realm

# [rest_api]

# [http_auth_backend:default_auth_backend]
# backend=metadata_cache

# [rest_routing]
# require_realm=default_auth_realm

# [rest_metadata_cache]
# require_realm=default_auth_realm