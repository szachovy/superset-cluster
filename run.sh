#!/bin/bash

display_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --mgmt-nodes <nodes>                    Comma-separated list of management node hostnames."
    echo "                                          Example: --mgmt-nodes node1,node2"
    echo
    echo "  --mysql-nodes <nodes>                   Comma-separated list of MySQL node hostnames."
    echo "                                          Example: --mysql-nodes node1,node2,node3"
    echo
    echo "  --virtual-ip-address <ip>               Virtual IP address for internal and external communication."
    echo "                                          Example: --virtual-ip-address 192.168.1.100"
    echo
    echo "  --virtual-network-interface <interface> Virtual network interface on management nodes to which"
    echo "                                          the virtual IP address is attached."
    echo "                                          Example: --virtual-network-interface eth0"
    echo
    echo "  --virtual-network-mask <mask>           Network mask for the virtual network gateway."
    echo "                                          Example: --virtual-network-mask 24"
    echo
    echo "  -h, --help                              Show this help message and exit."
    echo
    echo "Example:"
    echo "  $0 \\"
    echo "     --mgmt-nodes node1,node2 \\"
    echo "     --mysql-nodes node3,node4,node5 \\"
    echo "     --virtual-ip-address 192.168.1.100 \\"
    echo "     --virtual-network-interface eth0 \\"
    echo "     --virtual-network-mask 24"
}


parse_arguments() {
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --mgmt-nodes)
                shift
                IFS=',' read -r -a mgmt_nodes <<< "$1"
                ;;
            --mysql-nodes)
                shift
                IFS=',' read -r -a mysql_nodes <<< "$1"
                ;;
            --virtual-ip-address)
                shift
                virtual_ip_address="$1"
                ;;
            --virtual-network-interface)
                shift
                virtual_network_interface="$1"
                ;;
            --virtual-network-mask)
                shift
                virtual_network_mask="$1"
                ;;
            -h|--help)
                display_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                display_help
                exit 1
                ;;
        esac
        shift
    done
}

parse_arguments "$@"

if python --version &>/dev/null; then
  eval "python ./src/initialize.py \
    '${virtual_ip_address}' \
    '${virtual_network_interface}' \
    '${virtual_network_mask}' \
    '${mgmt_nodes[*]}' \
    '${mysql_nodes[*]}'"
elif python3 --version &>/dev/null; then
  eval "python3 ./src/initialize.py \
    '${virtual_ip_address}' \
    '${virtual_network_interface}' \
    '${virtual_network_mask}' \
    '${mgmt_nodes[*]}' \
    '${mysql_nodes[*]}'"
else
  echo "Neither python nor python3 is set as the main executable in this environment, check python location with 'which python'."
  exit 1
fi
