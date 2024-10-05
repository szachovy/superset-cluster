import base64
import ipaddress
import sys
import re
import socket

import crypto
import decorators
import remote
import container_connection

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
        self.ca_key = self.generate_private_key()
        self.ca_certificate = self.generate_certificate('Superset-Cluster', self.ca_key)
        self.mysql()
        self.mgmt()
        self.superset()

    def mysql(self):
        mysql_root_password = self.generate_mysql_root_password()
        self.mysql_server_certificate = []
        self.mysql_node_keys = {}
        self.mysql_node_csrs = {}
        self.mysql_node_certificates = {}
        for node in self.mysql_nodes:
            controller = remote.Remote(node)
            self.mysql_node_keys[node] = self.generate_private_key()
            self.mysql_node_csrs[node] = self.generate_csr(f'{node}-mysql-server', self.mysql_node_keys[node])
            self.mysql_node_certificates[node] = self.generate_certificate(f'{node}-mysql-server', self.mysql_node_csrs[node], self.ca_key)
            controller.ssh_client.close()
            controller.sftp_client.close()
        for node in self.mysql_nodes:
            controller = remote.Remote(node)
            # mysql_node_key = self.generate_private_key()
            # mysql_node_csr = self.generate_csr(f'{node}-mysql-server', mysql_node_key)
            # mysql_node_certificate = self.generate_certificate(f'{node}-mysql-server', mysql_node_csr, self.ca_key)
            controller.create_directory('/opt/superset-cluster')
            controller.upload_directory(local_directory_path='./services/mysql-server', remote_directory_path='/opt/superset-cluster/mysql-server')
            controller.upload_file(content=mysql_root_password, remote_file_path='/opt/superset-cluster/mysql-server/mysql_root_password')
            controller.upload_file(content=self.deserialization(self.ca_key), remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem')
            controller.upload_file(content=self.deserialization(self.mysql_node_certificates['node-2']) + self.deserialization(self.mysql_node_certificates['node-3']) + self.deserialization(self.mysql_node_certificates['node-4']) + self.deserialization(self.ca_certificate), remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem')
            controller.upload_file(content=self.deserialization(self.mysql_node_keys[node]), remote_file_path='/opt/superset-cluster/mysql-server/mysql_server_key.pem')
            controller.upload_file(content=self.deserialization(self.mysql_node_certificates[node]), remote_file_path='/opt/superset-cluster/mysql-server/mysql_server_certificate.pem')
            controller.run_python_command("ContainerUtilities(container='mysql').run_mysql_server()")
            if node == self.mysql_nodes[0]:
                output = controller.run_python_command("print(ContainerUtilities(container='mysql').run_command_on_the_container('/opt/store_credentials.exp {mysql_nodes}', 'root', {{'MYSQL_TEST_LOGIN_FILE': '/var/run/mysqld/.mylogin.cnf'}}))".format(mysql_nodes=" ".join(self.mysql_nodes)))
                self.mylogin_cnf = base64.b64decode(output[2:-2].replace('\\n', ''))
                # print(output[2:-2].replace('\\n', ''))
                if len(self.mylogin_cnf) < 200:
                    output = controller.run_python_command("print(ContainerUtilities(container='mysql').run_command_on_the_container('/opt/store_credentials.exp {mysql_nodes}', 'root', {{'MYSQL_TEST_LOGIN_FILE': '/var/run/mysqld/.mylogin.cnf'}}))".format(mysql_nodes=" ".join(self.mysql_nodes)))
                    self.mylogin_cnf = base64.b64decode(output[2:-2].replace('\\n', ''))  #if below 200 bytes, regenerate
            # self.mysql_server_certificate.append(mysql_node_certificate)
            controller.ssh_client.close()
            controller.sftp_client.close()
            # exit(0)

    def mgmt(self):
        #openssl verify -CAfile superset_cluster_ca_certificate.pem mysql_server_certificate.pem
        self.mysql_superset_password = self.generate_mysql_superset_password()
        state="MASTER"
        priority=100
        for node in self.mgmt_nodes:
            controller = remote.Remote(node)
            controller.create_directory('/opt/superset-cluster')
            mgmt_node_key = self.generate_private_key()
            mgmt_node_csr = self.generate_csr(f'{node}-mysql-mgmt', mgmt_node_key)
            mgmt_node_certificate = self.generate_certificate(f'{node}-mysql-mgmt', mgmt_node_csr, self.ca_key)
            controller.upload_directory(local_directory_path='./services/mysql-mgmt', remote_directory_path='/opt/superset-cluster/mysql-mgmt')
            controller.upload_file(content=self.mysql_superset_password, remote_file_path='/opt/superset-cluster/mysql-mgmt/mysql_superset_password')
            controller.upload_file(content=self.mylogin_cnf, remote_file_path='/opt/superset-cluster/mysql-mgmt/.mylogin.cnf')
            controller.change_permissions_to_root('/opt/superset-cluster/mysql-mgmt/.mylogin.cnf')
            controller.upload_file(content=self.deserialization(self.ca_key), remote_file_path='/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_key.pem')
            controller.upload_file(content=self.deserialization(self.mysql_node_certificates['node-2']) + self.deserialization(self.mysql_node_certificates['node-3']) + self.deserialization(self.mysql_node_certificates['node-4']) + self.deserialization(mgmt_node_certificate) + self.deserialization(self.ca_certificate), remote_file_path='/opt/superset-cluster/mysql-mgmt/superset_cluster_ca_certificate.pem')
            controller.upload_file(content=self.deserialization(mgmt_node_key), remote_file_path='/opt/superset-cluster/mysql-mgmt/mysql_router_key.pem')
            controller.upload_file(content=self.deserialization(mgmt_node_certificate), remote_file_path='/opt/superset-cluster/mysql-mgmt/mysql_router_certificate.pem')
            controller.run_python_command("ContainerUtilities(container='mysql-mgmt').run_mysql_mgmt('{virtual_ip_address}', '{virtual_network_mask}', '{virtual_network_interface}', '{primary_mysql_node}', '{secondary_first_mysql_node}', '{secondary_second_mysql_node}', '{state}', '{priority}')".format(virtual_ip_address=self.virtual_ip_address,virtual_network_mask=self.virtual_network_mask,virtual_network_interface=self.virtual_network_interface,primary_mysql_node=self.mysql_nodes[0],secondary_first_mysql_node=self.mysql_nodes[1],secondary_second_mysql_node=self.mysql_nodes[2],state=state,priority=priority))
            state="BACKUP"
            priority=90
            controller.ssh_client.close()
            controller.sftp_client.close()

    
    def superset(self):
        superset_secret_key = self.generate_superset_secret_key()
        # self.mysql_superset_password = 'wjhkktlbtpal'
        for node in self.mgmt_nodes:
            controller = remote.Remote(node)
            superset_node_key = self.generate_private_key()
            superset_node_csr = self.generate_csr(f'{self.virtual_ip_address}', superset_node_key)
            superset_node_certificate = self.generate_certificate(f'{self.virtual_ip_address}', superset_node_csr, self.ca_key)
            controller.upload_directory(local_directory_path='./services/superset', remote_directory_path='/opt/superset-cluster/superset')
            controller.upload_file(content=self.deserialization(self.ca_key), remote_file_path='/opt/superset-cluster/superset/superset_cluster_ca_key.pem')
            controller.upload_file(content=self.deserialization(self.ca_certificate), remote_file_path='/opt/superset-cluster/superset/superset_cluster_ca_certificate.pem')
            controller.upload_file(content=self.deserialization(superset_node_key), remote_file_path='/opt/superset-cluster/superset/superset_cluster_key.pem')
            controller.upload_file(content=self.deserialization(superset_node_certificate), remote_file_path='/opt/superset-cluster/superset/superset_cluster_certificate.pem')
            print(f'PASSWORD {self.mysql_superset_password}')
            controller.run_python_command("ContainerUtilities(container='superset').run_superset('{virtual_ip_address}', '{superset_secret_key}', '{mysql_superset_password}')".format(virtual_ip_address=self.virtual_ip_address, superset_secret_key=superset_secret_key, mysql_superset_password=self.mysql_superset_password))
            controller.ssh_client.close()
            controller.sftp_client.close()
            # exit(0)
            


if __name__ == "__main__":
    Controller()