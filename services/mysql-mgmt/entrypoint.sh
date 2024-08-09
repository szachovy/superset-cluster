#!/bin/bash

set -euo pipefail

if [ "${IS_PRIMARY_MGMT_NODE}" = "true" ]; then
  export STATE="MASTER"
  export PRIORITY="100"

  for mysql_node_ip_address in "${PRIMARY_MYSQL_NODE}" "${SECONDARY_FIRST_MYSQL_NODE}" "${SECONDARY_SECOND_MYSQL_NODE}"; do
    mysqlsh --login-path="${mysql_node_ip_address}" --execute="dba.configureInstance('${mysql_node_ip_address}')"
  done

  mysqlsh --login-path="${PRIMARY_MYSQL_NODE}" --execute="dba.createCluster('superset');"

  for secondary_node_ip in "${SECONDARY_FIRST_MYSQL_NODE}" "${SECONDARY_SECOND_MYSQL_NODE}"; do
    mysqlsh --login-path="${secondary_node_ip}" --sql --execute="RESET MASTER;"
    mysqlsh --login-path="${PRIMARY_MYSQL_NODE}" --execute="dba.getCluster('superset').addInstance('${secondary_node_ip}',{recoveryMethod:'incremental'});"
  done

  mysqlsh --login-path="${PRIMARY_MYSQL_NODE}" --sql --file="/opt/superset-user.sql"
else
  export STATE="BACKUP"
  export PRIORITY="90"
fi

mysqlrouter --user "superset" --bootstrap "superset:cluster@${PRIMARY_MYSQL_NODE}:3306" --directory "/opt/initcontainer/mysql_router" --conf-use-sockets
/opt/envsubst-Linux-x86_64 < "/opt/keepalived.conf.tpl" > "/opt/initcontainer/keepalived.conf"
chown "superset:superset" "/opt/initcontainer/keepalived.conf"
