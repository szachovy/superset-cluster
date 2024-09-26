#!/bin/bash

mgmt_nodes=("wiktor-min-deblike" "wiktor-min-rhlike")
mysql_nodes=("wiktor-min-build" "wiktor-cli-sles" "wiktor-minssh-sles")
superset_network_interface="enp1s0"

virtual_ip_address="10.145.211.180"
virtual_network_interface="ens3"
virtual_ip_address_mask="22"

VIRTUAL_NETWORK="10.145.208.0/22"  # do it in common via python

_path_to_root_catalog="."

source ${_path_to_root_catalog}/src/common.sh

initialize_nodes
