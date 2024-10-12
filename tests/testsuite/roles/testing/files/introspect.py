"""
temporary
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
