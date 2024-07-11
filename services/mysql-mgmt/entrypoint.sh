#!/bin/bash

set -euo pipefail

if [ "${IS_SETUP}" == "true" ]; then
  if [ "${IS_PRIMARY_MGMT_NODE}" == "true" ]; then
    for mysql_node_ip_address in "${PRIMARY_MYSQL_NODE}" "${SECONDARY_FIRST_MYSQL_NODE}" "${SECONDARY_SECOND_MYSQL_NODE}"; do
      mysqlsh --login-path="${mysql_node_ip_address}" --execute="dba.configureInstance('${mysql_node_ip_address}')"
      sleep 15
    done

    mysqlsh --login-path="${PRIMARY_MYSQL_NODE}" --execute="dba.createCluster('superset');"
    sleep 15
    for secondary_node_ip in "${SECONDARY_FIRST_MYSQL_NODE}" "${SECONDARY_SECOND_MYSQL_NODE}"; do
      mysqlsh --login-path="${secondary_node_ip}" --sql --execute="RESET MASTER;"
      mysqlsh --login-path="${PRIMARY_MYSQL_NODE}" --execute="dba.getCluster('superset').addInstance('${secondary_node_ip}',{recoveryMethod:'incremental'});"
      sleep 60
    done
    mysqlsh --login-path="${PRIMARY_MYSQL_NODE}" --sql --file=/opt/mysqlrouter-grants.sql
  fi
  mysqlrouter --user "root" --bootstrap "superset:mysql@${PRIMARY_MYSQL_NODE}:3306" --directory "/opt/mysql_router" --conf-use-sockets
fi

if [ "${IS_PRIMARY_MGMT_NODE}" == "true" ]; then
  STATE="MASTER"
  PRIORITY="100"
else
  STATE="BACKUP"
  PRIORITY="90"
fi
export STATE PRIORITY
envsubst < "/opt/keepalived.conf.tpl" > "/etc/keepalived/keepalived.conf"

keepalived --use-file "/etc/keepalived/keepalived.conf"
mysqlrouter --config "/opt/mysql_router/mysqlrouter.conf"

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

