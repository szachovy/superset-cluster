
import ipaddress
import socket
import subprocess

import data_structures
import interfaces


class ContainerChecks(metaclass=data_structures.Overlay):
    def __init__(self, node_prefix: str, network_interface: str) -> None:
        self.node_prefix: str = node_prefix
        self.network_interface: str = network_interface
        self.nodes: int = 6

    @data_structures.Overlay.post_init_hook
    def status_services(self) -> None | AssertionError:
        assert subprocess.run(['service', 'ssh', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0, f'SSH service is not running in {socket.gethostname()} node'
        assert subprocess.run(['service', 'docker', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0, f'Docker service is not running in {socket.gethostname()} node'

    @data_structures.Overlay.post_init_hook
    def status_dns(self) -> None | AssertionError:
        for node_number in range(self.nodes):
            assert bool(ipaddress.IPv4Address(socket.gethostbyname(f"{self.node_prefix}-{node_number}"))), f"{self.node_prefix}-{node_number} node can not be resolved."

    @data_structures.Overlay.post_init_hook
    def status_network_interfaces(self) -> None | AssertionError:
        assert socket.gethostbyaddr(interfaces.network_interfaces(network_interface=self.network_interface))[0] == socket.gethostname(), 'Hostname does not resolve to IPv4 address of the node taken from the configuration'
