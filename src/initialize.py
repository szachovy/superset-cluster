import base64
import ipaddress
import itertools
import sys
import re
import socket

import crypto
import decorators
import remote

if len(sys.argv) != 6:
    print("Error: Invalid form of arguments provided.")
    sys.exit(1)


@decorators.Overlay.run_all_methods
class ArgumentParser:
    def validate_virtual_ip_address(self) -> None:
        try:
            socket.inet_aton(sys.argv[1])
        except socket.error:
            raise ValueError('Invalid virtual-ip-address provided.') 
        self.virtual_ip_address = sys.argv[1]

    def validate_virtual_network_mask(self) -> None:
        try:
            try:
                network_mask: int = ipaddress.IPv4Network(f'0.0.0.0/{sys.argv[3]}').prefixlen
            except ipaddress.NetmaskValueError:
                raise ValueError
            if 0 <= network_mask <= 32:
                self.virtual_network_mask = network_mask
        except ValueError:
            raise ValueError('Invalid virtual-network-mask provided.')

    def validate_virtual_network_interface(self) -> None:
        if re.match(r"^[a-zA-Z0-9_-]+$", sys.argv[2]) is not None:
            self.virtual_network_interface = sys.argv[2]
        else:
            raise ValueError('Invalid virtual-network-interface provided.')

    def validate_nodes(self) -> None:
        self.mgmt_nodes = []
        self.mysql_nodes = []

        def validate_hostname(hostname: str) -> str:
            """(RFC 1123 compliance)."""
            allowed_characters = re.compile(r"[A-Z\d-]{1,63}", re.IGNORECASE)
            if not ((len(hostname) > 255) or ("." in hostname)):
                if all(allowed_characters.match(x) for x in hostname):
                    return hostname
            raise ValueError(f'Invalid node hostname provided.')
        
        for mgmt_node in (node for mgmt_node in sys.argv[4].split(',') for node in mgmt_node.split(' ')):
            self.mgmt_nodes.append(validate_hostname(mgmt_node))
        for mysql_node in (node for mysql_node in sys.argv[5].split(',') for node in mysql_node.split(' ')):
            self.mysql_nodes.append(validate_hostname(mysql_node))


class Controller(ArgumentParser, metaclass=decorators.Overlay):
    def __init__(self) -> None:
        super().__init__()
        self.mysql_nodes = [remote.RemoteConnection(node) for node in self.mysql_nodes]
        self.mgmt_nodes = [remote.RemoteConnection(node) for node in self.mgmt_nodes]
        self.cert_manager = crypto.OpenSSL()

    @decorators.Overlay.run_selected_methods_once
    def credentials(self):
        self.ca_key = self.cert_manager.generate_private_key()
        self.ca_certificate = self.cert_manager.generate_certificate('Superset-Cluster', self.ca_key)
        self.mysql_root_password = self.cert_manager.generate_mysql_root_password()
        self.mysql_superset_password = self.cert_manager.generate_mysql_superset_password()
        self.superset_secret_key = self.cert_manager.generate_superset_secret_key()
        for node in list(itertools.chain(self.mysql_nodes, self.mgmt_nodes)):
            node.key = self.cert_manager.generate_private_key()
            node.csr = self.cert_manager.generate_csr(f'Superset-Cluster-{node.node}', node.key)
            node.certificate = self.cert_manager.generate_certificate(f'Superset-Cluster-{node.node}', node.csr, self.ca_key)
            node.create_directory('/opt/superset-cluster')
        for node in self.mgmt_nodes:
            node.superset_key = self.cert_manager.generate_private_key()
            node.superset_csr = self.cert_manager.generate_csr(self.virtual_ip_address, node.superset_key)
            node.superset_certificate = self.cert_manager.generate_certificate(self.virtual_ip_address, node.superset_csr, self.ca_key)

    def get_mylogin_cnf(self, node: remote.RemoteConnection) -> str | ValueError:
        for _ in range(3):
            output = node.run_python_container_command("print(ContainerConnection(container='mysql').run_command_on_the_container('/opt/store_credentials.exp {mysql_nodes}', 'root', {{'MYSQL_TEST_LOGIN_FILE': '/var/run/mysqld/.mylogin.cnf'}}))".format(mysql_nodes=" ".join(node.node for node in self.mysql_nodes)))['output']
            mylogin_cnf = base64.b64decode(output[2:-2].replace('\\n', ''))
            if len(mylogin_cnf) > 300:
                return mylogin_cnf
        raise ValueError('Fetched MYSQL_TEST_LOGIN_FILE invalid')

    def start_mysql_servers(self):
        for node in self.mysql_nodes:
            node.upload_directory(local_directory_path='./services/mysql-server', remote_directory_path='/opt/superset-cluster/mysql-server')
            node.upload_file(content=self.mysql_root_password, remote_file_path='/opt/superset-cluster/mysql-server/mysql_root_password')
            node.upload_file(content=self.cert_manager.deserialization(self.ca_key), remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem')
            node.upload_file(content=''.join(self.cert_manager.deserialization(node.certificate) for node in self.mysql_nodes) + self.cert_manager.deserialization(self.ca_certificate), remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem')
            node.upload_file(content=self.cert_manager.deserialization(node.key), remote_file_path='/opt/superset-cluster/mysql-server/mysql_server_key.pem')
            node.upload_file(content=self.cert_manager.deserialization(node.certificate), remote_file_path='/opt/superset-cluster/mysql-server/mysql_server_certificate.pem')
            node.run_python_container_command("ContainerConnection(container='mysql').run_mysql_server()")
            if node == self.mysql_nodes[0]:
                self.mylogin_cnf = self.get_mylogin_cnf(node)


    def start_mysql_mgmt(self, node: remote.RemoteConnection, state: str, priority: int):
        node.upload_directory(local_directory_path='./services/mysql-mgmt', remote_directory_path='/opt/superset-cluster/mysql-mgmt')
        node.upload_file(content=self.mysql_superset_password, remote_file_path='/opt/superset-cluster/mysql-mgmt/mysql_superset_password')
        node.upload_file(content=self.mylogin_cnf, remote_file_path='/opt/superset-cluster/mysql-mgmt/.mylogin.cnf')
        node.change_permissions_to_root('/opt/superset-cluster/mysql-mgmt/.mylogin.cnf')
        node.upload_file(content=self.cert_manager.deserialization(self.ca_key), remote_file_path='/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_key.pem')
        node.upload_file(content=''.join(self.cert_manager.deserialization(node.certificate) for node in self.mysql_nodes) + self.cert_manager.deserialization(self.ca_certificate), remote_file_path='/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_certificate.pem')
        node.upload_file(content=self.cert_manager.deserialization(node.key), remote_file_path='/opt/superset-cluster/mysql-mgmt/mysql_router_key.pem')
        node.upload_file(content=self.cert_manager.deserialization(node.certificate), remote_file_path='/opt/superset-cluster/mysql-mgmt/mysql_router_certificate.pem')
        node.run_python_container_command("ContainerConnection(container='mysql-mgmt').run_mysql_mgmt('{virtual_ip_address}', '{virtual_network_mask}', '{virtual_network_interface}', '{primary_mysql_node}', '{secondary_first_mysql_node}', '{secondary_second_mysql_node}', '{state}', '{priority}')"
            .format(
                virtual_ip_address=self.virtual_ip_address,
                virtual_network_mask=self.virtual_network_mask,
                virtual_network_interface=self.virtual_network_interface,
                primary_mysql_node=self.mysql_nodes[0].node,
                secondary_first_mysql_node=self.mysql_nodes[1].node,
                secondary_second_mysql_node=self.mysql_nodes[2].node,
                state=state,
                priority=priority
              )
        )
    
    def start_superset(self):
        for node in self.mgmt_nodes:
            node.upload_directory(local_directory_path='./services/superset', remote_directory_path='/opt/superset-cluster/superset')
            node.upload_file(content=self.cert_manager.deserialization(self.ca_key), remote_file_path='/opt/superset-cluster/superset/superset_cluster_ca_key.pem')
            node.upload_file(content=self.cert_manager.deserialization(self.ca_certificate), remote_file_path='/opt/superset-cluster/superset/superset_cluster_ca_certificate.pem')
            node.upload_file(content=self.cert_manager.deserialization(node.superset_key), remote_file_path='/opt/superset-cluster/superset/superset_cluster_key.pem')
            node.upload_file(content=self.cert_manager.deserialization(node.superset_certificate), remote_file_path='/opt/superset-cluster/superset/superset_cluster_certificate.pem')
            node.run_python_container_command("ContainerConnection(container='superset').run_superset('{virtual_ip_address}', '{superset_secret_key}', '{mysql_superset_password}')"
                .format(
                    virtual_ip_address=self.virtual_ip_address,
                    superset_secret_key=self.superset_secret_key,
                    mysql_superset_password=self.mysql_superset_password
                )
            )
            
    def start_cluster(self):
        try:
            self.start_mysql_servers()
            self.start_mysql_mgmt(node=self.mgmt_nodes[0], state="MASTER", priority=100)
            self.start_mysql_mgmt(node=self.mgmt_nodes[1], state="BACKUP", priority=90)
            self.start_superset()
        finally:
            for node in list(itertools.chain(self.mysql_nodes, self.mgmt_nodes)):
                node.ssh_client.close()
                node.sftp_client.close()

if __name__ == "__main__":
    Controller().start_cluster()
