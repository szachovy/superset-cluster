#!/bin/bash

set -euo pipefail

# echo "100 keepalived" | tee -a /etc/iproute2/rt_tables
# /24
# ip addr add ${VIRTUAL_IP_ADDRESS} dev ${VIRTUAL_NETWORK_INTERFACE}
# ip addr del ${VIRTUAL_IP_ADDRESS} dev ${VIRTUAL_NETWORK_INTERFACE}
# ip route add default via 172.18.0.1 dev ${VIRTUAL_NETWORK_INTERFACE} src 172.18.0.8

# ip route replace 172.18.0.0/16 dev eth0 proto kernel scope link src 172.18.0.8
# ip route add default 172.18.0.0/16 dev eth0 src 172.18.0.2
# echo "100 custom_table" | tee -a /etc/iproute2/rt_tables
# ip route add default via 172.18.0.1 dev ${VIRTUAL_NETWORK_INTERFACE} table custom_table
# ip rule add from ${VIRTUAL_IP_ADDRESS} table custom_table

# 172.18.0.0/16 src ${VIRTUAL_IP_ADDRESS} metric 1 dev eth0 scope link
# ip route replace 172.18.0.0/16 dev eth0 proto kernel scope link src 172.18.0.2 metric 2
# ip route del 172.18.0.0/16 dev eth0 proto kernel scope link src 172.18.0.2

#     virtual_routes {
#          172.18.0.0/16 dev eth0 table keepalived
#          default via 172.18.0.1 dev eth0 table keepalived
# #        172.18.0.0/16 src ${VIRTUAL_IP_ADDRESS} metric 50 dev eth0 scope link
#     }
#     virtual_rules {
#         from 172.18.0.8 table keepalived
#     }

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

  /opt/envsubst-Linux-x86_64 < "/opt/superset-user.sql.tpl" > "/opt/superset-user.sql"
  mysqlsh --login-path="${PRIMARY_MYSQL_NODE}" --sql --file="/opt/superset-user.sql"
else
  export STATE="BACKUP"
  export PRIORITY="90"
fi

# sleep infinity

ifmetric ${VIRTUAL_NETWORK_INTERFACE} 2
/opt/envsubst-Linux-x86_64 < "/opt/keepalived.conf.tpl" > "/opt/default/keepalived.conf";
chown superset:superset "/opt/default"

# THERE IS NO PYTHON
# export VIRTUAL_NETWORK=$(python3 -c "import ipaddress; print(ipaddress.IPv4Interface('${VIRTUAL_IP_ADDRESS}/${VIRTUAL_IP_ADDRESS_MASK}').network)")

# ip addr add ${VIRTUAL_IP_ADDRESS}/${VIRTUAL_IP_ADDRESS_MASK} dev ${VIRTUAL_NETWORK_INTERFACE}
# ip route add ${VIRTUAL_NETWORK} src ${VIRTUAL_IP_ADDRESS} metric 1 dev ${VIRTUAL_NETWORK_INTERFACE} scope link
# mysqlrouter --user "superset" --bootstrap "superset:cluster@${PRIMARY_MYSQL_NODE}:3306" --directory "/opt/default/mysql_router" --conf-use-sockets
# ip addr del ${VIRTUAL_IP_ADDRESS}/${VIRTUAL_IP_ADDRESS_MASK} dev ${VIRTUAL_NETWORK_INTERFACE}
# chown "superset:superset" "/opt/default/keepalived.conf"
