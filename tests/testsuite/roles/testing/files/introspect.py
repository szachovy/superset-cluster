
import argparse
import os
import socket

import interfaces

# python3 introspect.py --nodes 5 --node-prefix node --network-interface eth0

class ArgumentParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)

        self.parser.add_argument('--nodes', type=int, required=True)
        self.parser.add_argument('--node-prefix', type=str, required=True)
        self.parser.add_argument('--network-interface', type=str, required=True)

    def parse_arguments(self):
        return self.parser.parse_args()


class ServiceNotRunningError(Exception):
    def __init__(self, service_name):
        super().__init__(f"The service '{service_name}' is not running.")


class ContainerChecks():
    def __init__(self):
        print(self.__repr__())
        self.arguments = ArgumentParser().parse_arguments()

    def __repr__(self) -> str:
        return f"Running checks on container {socket.gethostname()}"

    @staticmethod
    def check_service(service: str):
        if os.system(f'service {service} status') != 0:
            raise ServiceNotRunningError(service)

    def check_dns(self):
        for node in range(self.arguments.nodes):
            host: str = f"{self.arguments.node_prefix}-{node}"
            try:
                print(f"{host} node IPv4 found: ", socket.gethostbyname(host))
            except socket.gaierror:
                print(f"{host} node can not be resolved.")
                raise

    def check_network_interface(self):
        try:
            print(f"{self.arguments.network_interface} IPv4 found: ", interfaces.network_interfaces(network_interface=self.arguments.network_interface))
        except StopIteration:
            raise

    def run(self):
        self.check_service('ssh')
        self.check_service('docker')
        self.check_dns()
        self.check_network_interface()


if __name__ == "__main__":
    ContainerChecks().run()
