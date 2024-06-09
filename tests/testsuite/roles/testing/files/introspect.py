
import argparse
import socket
import subprocess

import interfaces


class ArgumentParser:
    def __init__(self) -> None:
        self.parser: argparse.ArgumentParser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)

        self.parser.add_argument('--nodes', type=int, required=True)
        self.parser.add_argument('--node-prefix', type=str, required=True)
        self.parser.add_argument('--network-interface', type=str, required=True)

    def parse_arguments(self) -> argparse.Namespace:
        return self.parser.parse_args()


class ServiceNotRunningError(Exception):
    def __init__(self, service_name: str) -> None:
        super().__init__(f"The service '{service_name}' is not running.")


class ContainerChecks:
    def __init__(self) -> None:
        self.arguments: argparse.Namespace = ArgumentParser().parse_arguments()
        print(self)
    
    def __str__(self) -> str:
        return f"Running checks on container {socket.gethostname()}"

    @staticmethod
    def check_service(service: str) -> None | ServiceNotRunningError:
        if subprocess.run(['service', service, 'status'],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).returncode != 0:
            raise ServiceNotRunningError(service)

    def check_dns(self) -> None | socket.gaierror:
        for node in range(self.arguments.nodes):
            host: str = f"{self.arguments.node_prefix}-{node}"
            try:
                socket.gethostbyname(host)
            except socket.gaierror as socketerror:
                if socketerror.errno == -2:
                    raise socket.gaierror(f"{host} node can not be resolved.")
                raise

    def check_network_interface(self) -> None | StopIteration:
        try:
            interfaces.network_interfaces(network_interface=self.arguments.network_interface)
        except StopIteration:
            raise

    def run(self) -> None:
        self.check_service('ssh')
        self.check_service('docker')
        self.check_dns()
        self.check_network_interface()


if __name__ == "__main__":
    ContainerChecks().run()
