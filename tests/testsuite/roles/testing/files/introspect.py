"""
Container Introspective Checks

This module provides the `ContainerChecks` class, which performs essential
service and network checks within a containerized or virtualized environment.

Classes:
--------
1. ContainerChecks:
    A class that conducts a series of health and configuration checks for
    container nodes. It verifies the status of services such as SSH and Docker,
    confirms that each node can be resolved through DNS, and checks network
    interface settings for correct hostname resolution.

Key Functionalities:
--------------------
- Service Status Verification: The `status_services` method checks whether
  essential services like SSH and Docker are running, and it raises an alert if
  they are not operational.

- DNS Resolution Validation: The `status_dns` method ensures that each node
  within the specified range can be resolved using DNS, thereby confirming that
  the nodes are reachable and correctly configured in the DNS server.

- Network Interface Configuration Check: The `status_network_interfaces`
  method verifies that the system hostname resolves to the correct IP address
  assigned to the specified network interface. This ensures that the node's
  hostname and IP configuration are consistent with the intended network setup.

Example Usage:
--------------
```python
ContainerChecks(
    node_prefix="node",
    virtual_network_interface="192.168.0.100"
)
"""

import ipaddress
import socket
import subprocess

import interfaces
import decorators


class ContainerChecks(metaclass=decorators.Overlay):
    def __init__(self, node_prefix: str, virtual_network_interface: str) -> None:
        self.node_prefix = node_prefix
        self.virtual_network_interface = virtual_network_interface
        self.nodes: int = 5

    @decorators.Overlay.run_selected_methods_once
    def status_services(self) -> None:
        assert \
            subprocess.run(
                [
                    'service',
                    'ssh',
                    'status'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            ).returncode == 0, \
            f'SSH service is not running in {socket.gethostname()} node'
        assert \
            subprocess.run(
                [
                    'service',
                    'docker',
                    'status'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            ).returncode == 0, \
            f'Docker service is not running in {socket.gethostname()} node'

    @decorators.Overlay.run_selected_methods_once
    def status_dns(self) -> None:
        for node_number in range(self.nodes):
            assert \
                bool(ipaddress.IPv4Address(socket.gethostbyname(f"{self.node_prefix}-{node_number}"))), \
                f"{self.node_prefix}-{node_number} node can not be resolved."

    @decorators.Overlay.run_selected_methods_once
    def status_network_interfaces(self) -> None:
        assert \
            socket.gethostbyaddr(interfaces.network_interfaces(network_interface=self.virtual_network_interface))[0] \
            == socket.gethostname(), \
            'Hostname does not resolve to IPv4 address of the node taken from the configuration'
