"""
Cluster Initialization Module

This module is responsible for initializing and managing a Superset cluster
environment, including the setup and configuration of MySQL servers, management
nodes, and Superset services within a distributed system.

Classes:
--------
- `ArgumentParser`:
  This class is responsible for parsing and validating command-line
  arguments related to the cluster configuration.

- `Controller`:
  This class manages the orchestration of the MySQL servers,
  management nodes, and the Superset service. It ensures that all
  components are properly configured, securely authenticated, and operationally
  ready to interact with each other over a specified network.

Key Functionalities:
--------------------
- Cluster Initialization: Sets up MySQL and management nodes, configures
  virtual IP settings, and initiates the Superset service.

- Secure Authentication: Uses OpenSSL for generating private keys and
  certificates required for secure communications between cluster components.

- Remote Management: Employs the remote connection routines for
  handling SSH/SFTP communications with nodes, including uploading
  directories/files and executing commands.

Example Usage:
--------------
This module is intended to run with the main program executable.
However, for the development purposes it is possible to run the code base
from the CLI given arguments in the sequence specified below:

1. Virtual IP address (e.g., "192.168.1.100")
2. Virtual network interface (e.g., "eth0")
3. Virtual network mask (e.g., "24")
4. Comma-separated list of management node hostnames (e.g., "mgmt1,mgmt2")
5. Comma-separated list of MySQL node hostnames (e.g., "mysql1,mysql2,mysql3")

```bash
python initialize.py 192.168.1.100 eth0 24 mgmt1,mgmt2 mysql1,mysql2,mysql3
```
"""

# pylint: disable=consider-using-f-string
# pylint: disable=attribute-defined-outside-init

import base64
import functools
import ipaddress
import itertools
import sys
import re
import socket

import crypto
import decorators
import remote


@decorators.Overlay.run_all_methods  # type: ignore[arg-type]
class ArgumentParser:
    def validate_virtual_ip_address(self) -> None:
        try:
            socket.inet_aton(sys.argv[1])
        except socket.error as socket_error:
            raise ValueError("Invalid virtual-ip-address provided") from socket_error
        self.virtual_ip_address = sys.argv[1]

    def validate_virtual_network_mask(self) -> None:
        try:
            try:
                network_mask: int = ipaddress.IPv4Network(f"0.0.0.0/{sys.argv[3]}").prefixlen
            except ipaddress.NetmaskValueError as netmask_value_error:
                raise ValueError from netmask_value_error
            if 0 <= network_mask <= 32:
                self.virtual_network_mask = network_mask
        except ValueError as error:
            raise ValueError("Invalid virtual-network-mask provided") from error

    def validate_virtual_network_interface(self) -> None:
        if re.match(r"^[a-zA-Z0-9_-]+$", sys.argv[2]) is not None:
            self.virtual_network_interface = sys.argv[2]
        else:
            raise ValueError("Invalid virtual-network-interface provided")

    def validate_nodes(self) -> None:
        self.mgmt_nodes = []
        self.mysql_nodes = []

        def validate_hostname(hostname: str) -> str:
            """(RFC 1123 compliance)."""
            allowed_characters = re.compile(r"[A-Z\d-]{1,63}", re.IGNORECASE)
            if not ((len(hostname) > 255) or ("." in hostname)):
                if all(allowed_characters.match(x) for x in hostname):
                    return hostname
            raise ValueError("Invalid node hostname provided")

        for mgmt_node in (node for mgmt_node in sys.argv[4].split(",") for node in mgmt_node.split(" ")):
            self.mgmt_nodes.append(validate_hostname(mgmt_node))
        for mysql_node in (node for mysql_node in sys.argv[5].split(",") for node in mysql_node.split(" ")):
            self.mysql_nodes.append(validate_hostname(mysql_node))


class Controller(ArgumentParser, metaclass=decorators.Overlay):
    # pylint: disable=too-many-instance-attributes
    def __init__(self) -> None:
        super().__init__()
        self.mysql_nodes: list[remote.RemoteConnection] = [
            remote.RemoteConnection(node) for node in self.mysql_nodes
        ]  # type: ignore[assignment]
        self.mgmt_nodes: list[remote.RemoteConnection] = [
            remote.RemoteConnection(node) for node in self.mgmt_nodes
        ]  # type: ignore[assignment]
        self.cert_manager = crypto.OpenSSL()

    def _recover_existing_credentials(self) -> bool:
        for node in self.mysql_nodes:
            try:
                _, stdout, _ = node.ssh_client.exec_command(
                    "cat /opt/superset-cluster/mysql-server/mysql_root_password"
                )
                password = stdout.read().decode().strip()
                if not password:
                    continue
                _, stdout, _ = node.ssh_client.exec_command(
                    "cat /opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem"
                )
                ca_key_pem = stdout.read().decode().strip()
                _, stdout, _ = node.ssh_client.exec_command(
                    "cat /opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem"
                )
                ca_bundle = stdout.read().decode().strip()
                if not (ca_key_pem and ca_bundle):
                    continue
                certs = ca_bundle.split('-----END CERTIFICATE-----')
                ca_cert_pem = [c for c in certs if '-----BEGIN CERTIFICATE-----' in c][-1]
                ca_cert_pem = ca_cert_pem.strip() + '\n-----END CERTIFICATE-----\n'
                self.ca_key = self.cert_manager.serialization(ca_key_pem)
                self.ca_certificate = self.cert_manager.serialization(ca_cert_pem)
                self.mysql_root_password = password
                break
            except (OSError, IndexError, ValueError):
                continue
        else:
            return False
        for node in self.mgmt_nodes:
            try:
                _, stdout, _ = node.ssh_client.exec_command(
                    "cat /opt/superset-cluster/mysql-mgmt/mysql_superset_password"
                )
                superset_pw = stdout.read().decode().strip()
                if not superset_pw:
                    continue
                _, stdout, _ = node.ssh_client.exec_command(
                    "docker exec $(docker ps --filter name=superset"
                    " --format '{{.ID}}' | head -1)"
                    " cat /run/secrets/superset_secret_key 2>/dev/null"
                )
                secret_key = stdout.read().decode().strip()
                if not secret_key:
                    continue
                self.mysql_superset_password = superset_pw
                self.superset_secret_key = secret_key
                return True
            except OSError:
                continue
        return False

    @decorators.Overlay.run_selected_methods_once
    def credentials(self) -> None:
        if not self._recover_existing_credentials():
            self.ca_key = self.cert_manager.generate_private_key()
            self.ca_certificate = self.cert_manager.generate_certificate('Superset-Cluster', self.ca_key)
            self.mysql_root_password = self.cert_manager.generate_mysql_root_password()
            self.mysql_superset_password = self.cert_manager.generate_mysql_superset_password()
            self.superset_secret_key = self.cert_manager.generate_superset_secret_key()
        for node in list(itertools.chain(self.mysql_nodes, self.mgmt_nodes)):
            node.key = self.cert_manager.generate_private_key()
            node.csr = self.cert_manager.generate_csr(f'Superset-Cluster-{node.node}', node.key)
            node.certificate = self.cert_manager.generate_certificate(f'Superset-Cluster-{node.node}',
                                                                      node.csr,
                                                                      self.ca_key)
            try:
                node.create_directory('/opt/superset-cluster')
            except IOError:
                pass
        for node in self.mgmt_nodes:
            node.superset_key = self.cert_manager.generate_private_key()
            node.superset_csr = self.cert_manager.generate_csr(self.virtual_ip_address, node.superset_key)
            node.superset_certificate = self.cert_manager.generate_certificate(self.virtual_ip_address,
                                                                               node.superset_csr,
                                                                               self.ca_key)

    @functools.lru_cache(maxsize=1)
    def get_mylogin_cnf(self, node: remote.RemoteConnection) -> bytes:
        for _ in range(3):
            output = node.run_python_container_command(
                "print( \
                    ContainerConnection( \
                        container='mysql' \
                    ).run_command_on_the_container( \
                        '/opt/store_credentials.exp {mysql_nodes}', \
                        'root', \
                        {{'MYSQL_TEST_LOGIN_FILE': '/var/run/mysqld/.mylogin.cnf'}} \
                    ) \
                )".format(
                    mysql_nodes=" ".join(node.node for node in self.mysql_nodes))
                )["output"]
            mylogin_cnf = base64.b64decode(output[2:-2].replace("\\n", ""))
            if len(mylogin_cnf) > 320:
                return mylogin_cnf
        raise ValueError("Fetched MYSQL_TEST_LOGIN_FILE invalid")

    def start_mysql_servers(self) -> None:
        for node in self.mysql_nodes:
            _, stdout, _ = node.ssh_client.exec_command(
                "docker inspect --format='{{.State.Health.Status}}'"
                " mysql 2>/dev/null"
            )
            if stdout.read().decode().strip() == "healthy":
                continue
            node.ssh_client.exec_command("docker rm -f mysql 2>/dev/null")
            node.upload_directory(
                local_directory_path="./services/mysql-server",
                remote_directory_path="/opt/superset-cluster/mysql-server"
            )
            node.upload_file(
                content=self.mysql_root_password,
                remote_file_path="/opt/superset-cluster/mysql-server/mysql_root_password"
            )
            node.upload_file(
                content=self.cert_manager.deserialization(self.ca_key),
                remote_file_path="/opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem")
            node.upload_file(
                content="".join(self.cert_manager.deserialization(node.certificate) for node in self.mysql_nodes)
                + self.cert_manager.deserialization(self.ca_certificate),
                remote_file_path="/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem"
            )
            node.upload_file(
                content=self.cert_manager.deserialization(node.key),
                remote_file_path="/opt/superset-cluster/mysql-server/mysql_server_key.pem"
            )
            node.upload_file(
                content=self.cert_manager.deserialization(node.certificate),
                remote_file_path="/opt/superset-cluster/mysql-server/mysql_server_certificate.pem"
            )
            node.run_python_container_command(
                "ContainerConnection( \
                    container='mysql' \
                ).run_mysql_server()"
            )

    def start_mysql_mgmt(self, node: remote.RemoteConnection, state: str, priority: int) -> None:
        _, stdout, _ = node.ssh_client.exec_command(
            "docker inspect --format='{{.State.Health.Status}}'"
            " mysql-mgmt 2>/dev/null"
        )
        if stdout.read().decode().strip() == "healthy":
            return
        node.ssh_client.exec_command(
            "docker rm -f mysql-mgmt mysql-mgmt-initcontainer 2>/dev/null;"
            " docker volume rm mysql-mgmt_default_generated 2>/dev/null"
        )
        node.upload_directory(
            local_directory_path="./services/mysql-mgmt",
            remote_directory_path="/opt/superset-cluster/mysql-mgmt"
        )
        node.upload_file(
            content=self.mysql_superset_password,
            remote_file_path="/opt/superset-cluster/mysql-mgmt/mysql_superset_password"
        )
        node.upload_file(
            content=self.get_mylogin_cnf(self.mysql_nodes[0]),
            remote_file_path="/opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
        )
        node.change_permissions_to_root(
            "/opt/superset-cluster/mysql-mgmt/.mylogin.cnf"
        )
        node.upload_file(
            content=self.cert_manager.deserialization(self.ca_key),
            remote_file_path="/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_key.pem"
        )
        node.upload_file(
            content="".join(self.cert_manager.deserialization(node.certificate) for node in self.mysql_nodes)
            + self.cert_manager.deserialization(self.ca_certificate),
            remote_file_path="/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_certificate.pem"
        )
        node.upload_file(
            content=self.cert_manager.deserialization(node.key),
            remote_file_path="/opt/superset-cluster/mysql-mgmt/mysql_router_key.pem"
        )
        node.upload_file(
            content=self.cert_manager.deserialization(node.certificate),
            remote_file_path="/opt/superset-cluster/mysql-mgmt/mysql_router_certificate.pem"
        )
        node.run_python_container_command(
            "ContainerConnection( \
                container='mysql-mgmt' \
            ).run_mysql_mgmt( \
                '{virtual_ip_address}', \
                '{virtual_network_mask}', \
                '{virtual_network_interface}', \
                '{primary_mysql_node}', \
                '{secondary_first_mysql_node}', \
                '{secondary_second_mysql_node}', \
                '{state}', \
                '{priority}' \
            )".format(virtual_ip_address=self.virtual_ip_address,
                      virtual_network_mask=self.virtual_network_mask,
                      virtual_network_interface=self.virtual_network_interface,
                      primary_mysql_node=self.mysql_nodes[0].node,
                      secondary_first_mysql_node=self.mysql_nodes[1].node,
                      secondary_second_mysql_node=self.mysql_nodes[2].node,
                      state=state,
                      priority=priority)
        )

    def start_superset(self) -> None:
        for node in self.mgmt_nodes:
            _, redis_out, _ = node.ssh_client.exec_command(
                "docker inspect --format='{{.State.Health.Status}}'"
                " redis 2>/dev/null"
            )
            _, svc_out, _ = node.ssh_client.exec_command(
                "docker service ps superset"
                " --format='{{.CurrentState}}'"
                " --filter desired-state=running 2>/dev/null"
            )
            redis_healthy = redis_out.read().decode().strip() == "healthy"
            superset_running = "Running" in svc_out.read().decode()
            if redis_healthy and superset_running:
                continue
            node.ssh_client.exec_command(
                "docker service rm superset 2>/dev/null;"
                " docker rm -f redis 2>/dev/null;"
                " docker swarm leave --force 2>/dev/null;"
                " docker network rm superset-network docker_gwbridge 2>/dev/null"
            )
            node.upload_directory(
                local_directory_path="./services/superset",
                remote_directory_path='/opt/superset-cluster/superset'
            )
            node.upload_file(
                content=self.cert_manager.deserialization(self.ca_key),
                remote_file_path="/opt/superset-cluster/superset/superset_cluster_ca_key.pem"
            )
            node.upload_file(
                content=self.cert_manager.deserialization(self.ca_certificate),
                remote_file_path="/opt/superset-cluster/superset/superset_cluster_ca_certificate.pem"
            )
            node.upload_file(
                content=self.cert_manager.deserialization(node.superset_key),
                remote_file_path="/opt/superset-cluster/superset/superset_cluster_key.pem"
            )
            node.upload_file(
                content=self.cert_manager.deserialization(node.superset_certificate),
                remote_file_path="/opt/superset-cluster/superset/superset_cluster_certificate.pem"
            )
            node.run_python_container_command(
                "ContainerConnection( \
                    container='superset' \
                ).run_superset( \
                    '{virtual_ip_address}', \
                    '{superset_secret_key}', \
                    '{mysql_superset_password}' \
                )".format(virtual_ip_address=self.virtual_ip_address,
                          superset_secret_key=self.superset_secret_key,
                          mysql_superset_password=self.mysql_superset_password)
            )

    def teardown_node(self, node: remote.RemoteConnection, is_mgmt: bool = False) -> None:
        commands = [
            "if docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null"
            " | grep -qvx inactive; then docker swarm leave --force; fi",
            "docker ps -aq | xargs -r docker rm -f",
            "docker volume ls -q | xargs -r docker volume rm",
            "docker network ls --filter name=superset-network -q"
            " | xargs -r docker network rm",
            "docker network ls --filter name=docker_gwbridge -q"
            " | xargs -r docker network rm",
            "if [ -d /opt/superset-cluster ]; then"
            " rm -rf /opt/superset-cluster; fi",
        ]
        if is_mgmt:
            commands.extend([
                "if ip addr show dev {iface} 2>/dev/null"
                " | grep -q '{vip}/'; then"
                " ip addr del {vip}/{mask} dev {iface}; fi".format(
                    iface=self.virtual_network_interface,
                    vip=self.virtual_ip_address,
                    mask=self.virtual_network_mask),
                "if ip route show | grep -q '{vip} '; then"
                " ip route del {vip}; fi".format(
                    vip=self.virtual_ip_address),
            ])
        _, stdout, stderr = node.ssh_client.exec_command(" && ".join(commands))
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError(
                f"Teardown failed on {node.node} (exit {exit_status}): "
                f"{stderr.read().decode().strip()}"
            )

    def start_cluster(self) -> None:
        try:
            self.start_mysql_servers()
            self.start_mysql_mgmt(node=self.mgmt_nodes[0], state="MASTER", priority=100)
            self.start_mysql_mgmt(node=self.mgmt_nodes[1], state="BACKUP", priority=90)
            self.start_superset()
        finally:
            for node in list(itertools.chain(self.mysql_nodes, self.mgmt_nodes)):
                node.ssh_client.close()
                node.sftp_client.close()

    def cleanup(self) -> None:
        try:
            for node in self.mgmt_nodes:
                try:
                    self.teardown_node(node, is_mgmt=True)
                except (OSError, RuntimeError):
                    pass
            for node in self.mysql_nodes:
                try:
                    self.teardown_node(node, is_mgmt=False)
                except (OSError, RuntimeError):
                    pass
        finally:
            for node in list(itertools.chain(self.mysql_nodes, self.mgmt_nodes)):
                node.ssh_client.close()
                node.sftp_client.close()


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Invalid form of arguments provided")
        sys.exit(1)

    action = sys.argv[6] if len(sys.argv) > 6 else "deploy"
    controller = Controller()

    if action == "cleanup":
        controller.cleanup()
    else:
        controller.start_cluster()
