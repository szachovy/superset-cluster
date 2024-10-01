#!/bin/bash

node_prefix="${1}"
virtual_ip_address="${2}"
virtual_network_mask="${3}"
virtual_network_interface="${4}"

VIRTUAL_NETWORK="172.18.0.0/16"  # do it in common via python

mgmt_nodes=("${node_prefix}-0" "${node_prefix}-1")
mysql_nodes=("${node_prefix}-2" "${node_prefix}-3" "${node_prefix}-4")

_path_to_root_catalog="../.."

source "${_path_to_root_catalog}/src/common.sh"
