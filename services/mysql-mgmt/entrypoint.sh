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
    mv /opt/.mylogin.cnf ${HOME}
    MYSQL_ROOT_PASSWORD="${4:-}"
    PRIMARY_MYSQL_NODE_IP="${5:-}"
    SECONDARY_MYSQL_NODES_IP="${6:-} ${7:-}"

    for mysql_node_ip_address in "${PRIMARY_MYSQL_NODE_IP}" ${SECONDARY_MYSQL_NODES_IP}; do
      mysqlsh --login-path="${mysql_node_ip_address}" --execute="dba.configureInstance('${mysql_node_ip_address}')"
      sleep 15
    done

    mysqlsh --login-path="${PRIMARY_MYSQL_NODE_IP}" --execute="dba.createCluster('superset');"
    sleep 15
    for secondary_node_ip in ${SECONDARY_MYSQL_NODES_IP}; do
      mysqlsh --login-path="${secondary_node_ip}" --sql --execute="RESET MASTER;"
      mysqlsh --login-path="${PRIMARY_MYSQL_NODE_IP}" --execute="dba.getCluster('superset').addInstance('${secondary_node_ip}',{recoveryMethod:'incremental'});"
      sleep 60
    done
  fi
  mysqlsh --login-path="${PRIMARY_MYSQL_NODE_IP}" --sql --file=/opt/mysqlrouter-grants.sql
  # mysqlrouter --user "root" --bootstrap "root:mysql@${PRIMARY_MYSQL_NODE_IP}:3306" --directory "/opt/mysql_router" --conf-use-sockets
  mysqlrouter --user "root" --bootstrap "superset:mysql@${PRIMARY_MYSQL_NODE_IP}:3306" --directory "/opt/mysql_router" --conf-use-sockets
fi

keepalived --use-file "/etc/keepalived/keepalived.conf" &
# mysqlrouter --config "/opt/mysql_router/mysqlrouter.conf" &

# SHOW VARIABLES LIKE 'gtid_executed';
# SHOW BINARY LOGS;
# RESET MASTER;
# RESET REPLICA ALL;
# SHOW BINLOG EVENTS IN 'binlog.000001';
# | binlog.000001 | 2938409 | Xid            |      8996 |     2938440 | COMMIT /* xid=8 */                                                |
# | binlog.000001 | 2938440 | Gtid           |      8996 |     2938517 | SET @@SESSION.GTID_NEXT= '39254785-3c3d-11ef-96a7-0242ac120004:6' |
# | binlog.000001 | 2938517 | Query          |      8996 |     2938653 | CREATE DATABASE IF NOT EXISTS `superset` /* xid=8893 */           |
# | binlog.000001 | 2938653 | Gtid           |      8996 |     2938732 | SET @@SESSION.GTID_NEXT= '39254785-3c3d-11ef-96a7-0242ac120004:7' |
# | binlog.000001 | 2938732 | Query          |      8996 |     2938947 | use `mysql`; CREATE USER 'mysql-user'@'%' IDENTIFIED WITH 'mysql_native_password' AS '*6C8989366EAF75BB670AD8EA7A7FC1176A95CEF4' /* xid=8896 */ |
# | binlog.000001 | 2938947 | Gtid           |      8996 |     2939024 | SET @@SESSION.GTID_NEXT= '39254785-3c3d-11ef-96a7-0242ac120004:8' |
# | binlog.000001 | 2939024 | Query          |      8996 |     2939193 | use `mysql`; GRANT ALL PRIVILEGES ON `superset`.* TO 'mysql-user'@'%' /* xid=8899 */ |
# | binlog.000001 | 2939193 | Stop           |      8996 |     2939216 |  

# CREATE DATABASE IF NOT EXISTS `superset`;
# CREATE USER 'superset' IDENTIFIED BY 'mysql' WITH GRANT OPTION;
# GRANT ALL PRIVILEGES ON `superset`.* TO 'superset';
# GRANT SELECT, INSERT ON mysql_innodb_cluster_metadata.* TO superset;
# GRANT SELECT ON performance_schema.* TO superset;
# GRANT CREATE ON *.* TO 'superset';

