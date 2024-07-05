#!/bin/bash

set -euo pipefail

PRIMARY_NODE="${1:-}"

if [ ! -f /etc/keepalived/keepalived.conf ]; then
  if [ "${PRIMARY_NODE}" == "true" ]; then
    STATE="MASTER"
    PRIORITY="100"
  else
    STATE="BACKUP"
    PRIORITY="90"
  fi
  VIRTUAL_IPADDRESS="${2:-}"
  INTERFACE="${3:-}"
  export STATE PRIORITY VIRTUAL_IPADDRESS INTERFACE
  envsubst < "/opt/keepalived.conf.tpl" > "/etc/keepalived/keepalived.conf"
fi

if [ ! -f /opt/mysql_router/mysqlrouter.conf ]; then
  if [ "${PRIMARY_NODE}" == "true" ]; then
    MYSQL_ROOT_PASSWORD="${4:-}"
    PRIMARY_MYSQL_NODE_IP="${5:-}"
    SECONDARY_MYSQL_NODES_IP="${6:-} ${7:-}"

    for mysql_node_ip_address in "${PRIMARY_MYSQL_NODE_IP}" ${SECONDARY_MYSQL_NODES_IP}; do
      mysqlsh --execute "dba.configureInstance('${mysql_node_ip_address}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false})"
      sleep 15
    done

    mysqlsh --uri "root:${MYSQL_ROOT_PASSWORD}@${PRIMARY_MYSQL_NODE_IP}:3306" --execute "dba.createCluster('superset');"
    sleep 15
    for secondary_node_ip in ${SECONDARY_MYSQL_NODES_IP}; do
      mysqlsh --uri "root:${MYSQL_ROOT_PASSWORD}@${PRIMARY_MYSQL_NODE_IP}:3306" --execute "dba.getCluster('superset').addInstance('root@${secondary_node_ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false,recoveryMethod:'incremental'});"
      sleep 60
    done
  fi
  mysqlrouter --user "root" --bootstrap "root:${MYSQL_ROOT_PASSWORD}@${PRIMARY_MYSQL_NODE_IP}:3306" --directory "/opt/mysql_router" --conf-use-sockets
fi

keepalived --use-file "/etc/keepalived/keepalived.conf" &
mysqlrouter --config "/opt/mysql_router/mysqlrouter.conf" &
