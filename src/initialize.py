import sys
import re
import socket

import crypto
import data_structures
import remote
import container_connection

if len(sys.argv) != 6:
    print("Error: Invalid form of arguments provided.")
    sys.exit(1)


@data_structures.Overlay.run_all_methods
class ArgumentParser:
    def validate_virtual_ip_address(self) -> None:
        try:
            socket.inet_aton(sys.argv[1])
        except socket.error:
            raise ValueError('Invalid virtual-ip-address provided.') 
        self.virtual_ip_address = sys.argv[1]

    def validate_virtual_network_mask(self) -> None:
        try:
            if 0 <= int(sys.argv[3]) <= 32:
                self.virtual_network_mask = sys.argv[3] 
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
            # allowed_characters = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
            allowed_characters = re.compile(r"[A-Z\d-]{1,63}", re.IGNORECASE)
            if not ((len(hostname) > 255) or ("." in hostname)):
                if all(allowed_characters.match(x) for x in hostname):
                    return hostname
            raise ValueError(f'Invalid node hostname provided.')
        
        for mgmt_node in (node for mgmt_node in sys.argv[4].split(',') for node in mgmt_node.split(' ')):
            self.mgmt_nodes.append(validate_hostname(mgmt_node))
        for mysql_node in (node for mysql_node in sys.argv[5].split(',') for node in mysql_node.split(' ')):
            self.mysql_nodes.append(validate_hostname(mysql_node))

class Controller(ArgumentParser, crypto.OpenSSL):
    def __init__(self) -> None:
        super().__init__()
        print(self.virtual_network_mask)
        print(self.virtual_ip_address)
        print(self.virtual_network_interface)
        print(self.mgmt_nodes)
        print(self.mysql_nodes)
        self.ca_key = self.generate_private_key()
        self.ca_certificate = self.generate_certificate('Superset-Cluster', self.ca_key)
        self.mysql()

    def mysql(self):
        mysql_root_password = self.generate_mysql_root_password()
        for node in self.mysql_nodes:
            controller = remote.Remote(node)
            mysql_node_key = self.generate_private_key()
            mysql_node_csr = self.generate_csr(f'{node}-mysql-server', mysql_node_key)
            mysql_node_certificate = self.generate_certificate(f'{node}-mysql-server', mysql_node_csr, self.ca_key)
            controller.upload_directory(local_directory_path='./services/mysql-server', remote_directory_path='/opt/superset-cluster/mysql-server')
            controller.upload_file(content=mysql_root_password, remote_file_path='/opt/superset-cluster/mysql-server/mysql_root_password')
            controller.upload_file(content=self.deserialization(self.ca_key), remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem')
            controller.upload_file(content=self.deserialization(self.ca_certificate), remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem')
            controller.upload_file(content=self.deserialization(mysql_node_key), remote_file_path='/opt/superset-cluster/mysql-server/mysql_server_key.pem')
            controller.upload_file(content=self.deserialization(mysql_node_certificate), remote_file_path='/opt/superset-cluster/mysql-server/mysql_server_certificate.pem')
            controller.run_command(f"ContainerUtilities(container='mysql').start()")
            controller.ssh_client.close()
            controller.sftp_client.close()
            exit(0)
    
    def mgmt(self):
        mysql_superset_password = self.generate_mysql_superset_password()
    
    def superset(self):
        pass

if __name__ == "__main__":
    Controller()