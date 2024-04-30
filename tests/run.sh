#!/bin/bash

NODES="${1}"

./setup/setup.sh ${NODES}
# ./run-testsuite/run.sh
# do not publish ports, with 8088 do iptables port forwarding (sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to <container_ip>:80)
