
import ast
import io
import ipaddress
import json
import random
import re
import socket
import subprocess
import tarfile
import os
import time

import docker
import requests


class ContainerUtilities:
    def __init__(self, container: str | None) -> None:
        self.client: docker.client.DockerClient = docker.from_env()
        self.container: str = container

    def run_command_on_the_container(self, command: str, user: str = 'superset', environment: dict = {}) -> bytes | requests.exceptions.RequestException:
        try:
            request: docker.models.containers.ExecResult = self.client.containers.get(self.container).exec_run(command, user=user, environment=environment, stdout=True, stderr=True)
        except (docker.errors.NotFound, docker.errors.APIError) as error:
            raise requests.exceptions.RequestException(f'Can not run commands on the container {self.container}: {error}')
        if request.exit_code != 0:
            raise requests.exceptions.RequestException(f'Command: {command} failed with exit code [{request.exit_code}] giving the following output: {request.output}')
        return request.output
    
    def info(self) -> dict:
        return self.client.info()
    
    def copy_file_to_the_container(self, host_filepath: str, container_dirpath: str) -> None:
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as archive:
            archive.add(host_filepath, arcname=os.path.basename(host_filepath))
        tar_stream.seek(0)
        self.client.containers.get(self.container).put_archive(container_dirpath, tar_stream.getvalue())
        tar_stream.close()

    @staticmethod
    def find_in_the_output(output: bytes, text: bytes) -> bool:
        return text in output

    def find_node_ip(self, node: str) -> str | socket.gaierror:
        try:
            return ipaddress.IPv4Address(socket.gethostbyname(node))
        except socket.gaierror as socketerror:
            if socketerror.errno == -2:
                raise socket.gaierror(f'Error finding IPv4 for node {node}: {socketerror}')
    
    @staticmethod
    def extract_session_cookie(request_output: bytes) -> str | ValueError:
        cookie_section: str | None = re.search(r'Set-Cookie: session=(.*?);', request_output.decode('utf-8'))
        if cookie_section:
            return cookie_section.group(1)
        raise ValueError(f'Session cookie in {request_output} has not been found')
    
    @staticmethod
    def decode_command_output(command: bytes) -> dict | ValueError:
        try:
            return ast.literal_eval(
                command.decode('utf-8')
                .replace('null', 'None')
                .replace('true', 'True')
                .replace('false', 'False')
            )
        except (ValueError, SyntaxError) as error:
            raise ValueError(f'Error decoding command {command} output: {error}')


    @staticmethod
    def calculate_virtual_network(virtual_ip_address: str, virtual_network_mask: str) -> str:
        return str(ipaddress.IPv4Interface(f"{virtual_ip_address}/{virtual_network_mask}").network)

    def wait_until_healthy(self, container_name, healthcheck_start_period, healthcheck_interval, healthcheck_retries):
        time.sleep(healthcheck_start_period)
        for container in self.client.containers.list(all=True):
            if container.name.startswith(container_name):
                for _ in range(healthcheck_retries):
                    if self.client.containers.get(container.name).attrs['State']['Health']['Status'] == 'healthy':
                        return True
                    time.sleep(healthcheck_interval)
        return False

    def run_mysql_server(self):
        # temporary
        import subprocess
        command = f'docker login ghcr.io -u szachovy -p ...'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        healthcheck_start_period = 90
        healthcheck_interval = 5
        healthcheck_retries = 3
        try:
            self.client.containers.run(
                "ghcr.io/szachovy/superset-cluster-mysql-server:latest",
                detach=True,
                name=self.container,
                hostname=socket.gethostname(),
                restart_policy={"Name": "always"},
                network="host",
                cap_add=["SYS_NICE"],
                #{"defaultAction":"SCMP_ACT_ALLOW","architectures":["SCMP_ARCH_X86_64"],"syscalls":[{"names":["kill"],"action":"SCMP_ACT_ERRNO"}]}
                security_opt=[f"seccomp={json.dumps(json.load(open('/opt/superset-cluster/mysql-server/seccomp.json')), separators=(',', ':'))}"],
                environment={
                    "MYSQL_INITDB_SKIP_TZINFO": "true",
                    "MYSQL_ROOT_PASSWORD_FILE": "/var/run/mysqld/mysql_root_password",
                    "SERVER_ID": random.randrange(1, 4294967296),
                    "HEALTHCHECK_START_PERIOD": 150
                },
                healthcheck = {
                    'test': ['CMD', 'mysqladmin', 'ping'],
                    'interval': healthcheck_interval * 1000000000,
                    'timeout': 10 * 1000000000,
                    'retries': healthcheck_retries,
                    'start_period': healthcheck_start_period * 1000000000
                },
                volumes={
                    "/opt/superset-cluster/mysql-server/mysql_root_password": {
                        'bind': '/var/run/mysqld/mysql_root_password'
                    },
                    "/opt/superset-cluster/mysql-server/mysql_server_certificate.pem": {
                        'bind': '/etc/mysql/ssl/mysql_server_certificate.pem',
                    },
                    "/opt/superset-cluster/mysql-server/mysql_server_key.pem": {
                        'bind': '/etc/mysql/ssl/mysql_server_key.pem',
                    },
                    "/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem": {
                        'bind': '/etc/mysql/ssl/superset_cluster_ca_certificate.pem',
                    }
                }
            )
        except docker.errors.APIError as e:
            print(f"Docker error {e}")
        
        self.wait_until_healthy('mysql', healthcheck_start_period, healthcheck_interval, healthcheck_retries)

    def run_mysql_mgmt(
            self,
            virtual_ip_address, 
            virtual_network_mask, 
            virtual_network_interface, 
            primary_mysql_node, 
            secondary_first_mysql_node, 
            secondary_second_mysql_node,
            state,
            priority):

        # temporary
        import subprocess
        command = f'docker login ghcr.io -u szachovy -p ...'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        healthcheck_start_period = 25
        healthcheck_interval = 5
        healthcheck_retries = 3
        os.environ["VIRTUAL_IP_ADDRESS"] = virtual_ip_address
        os.environ["VIRTUAL_NETWORK_MASK"] = virtual_network_mask
        os.environ["VIRTUAL_NETWORK_INTERFACE"] = virtual_network_interface
        os.environ["VIRTUAL_NETWORK"] = self.calculate_virtual_network(virtual_ip_address, virtual_network_mask)
        os.environ["PRIMARY_MYSQL_NODE"] = primary_mysql_node
        os.environ["SECONDARY_FIRST_MYSQL_NODE"] = secondary_first_mysql_node
        os.environ["SECONDARY_SECOND_MYSQL_NODE"] = secondary_second_mysql_node
        os.environ["HEALTHCHECK_START_PERIOD"] = healthcheck_start_period
        os.environ["HEALTHCHECK_INTERVAL"] = healthcheck_interval
        os.environ["HEALTHCHECK_RETRIES"] = healthcheck_retries
        os.environ["STATE"] = state
        os.environ["PRIORITY"] = priority
 
        result = subprocess.run(
            "docker compose --file /opt/superset-cluster/mysql-mgmt/docker_compose.yml up initcontainer && \
            docker compose --file /opt/superset-cluster/mysql-mgmt/docker_compose.yml up maincontainer --detach",
            capture_output=True,
            text=True,
            shell=True  # Use shell to interpret the command properly
        )

        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
    
        self.wait_until_healthy('mysql-mgmt', healthcheck_start_period, healthcheck_interval, healthcheck_retries)

    def run_superset(self, virtual_ip_address, superset_secret_key, mysql_superset_password):
        #temporary
        import subprocess
        command = f'docker login ghcr.io -u szachovy -p ...'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.client.swarm.init(advertise_addr=virtual_ip_address)
        self.client.networks.create(name='superset-network', driver='overlay', attachable=True)
        superset_secret_key_id = self.client.secrets.create(name='superset_secret_key', data=superset_secret_key).id
        mysql_superset_password_id = self.client.secrets.create(name='mysql_superset_password', data=mysql_superset_password).id


        healthcheck_start_period = 10
        healthcheck_interval = 10
        healthcheck_retries = 5

        self.client.containers.run(
            "redis",
            detach=True,
            restart_policy={"Name": "always"},
            name="redis",
            hostname="redis",
            network="superset-network",
            healthcheck={
                'test': ["CMD", "redis-cli", "ping"],
                'interval': healthcheck_interval * 1000000000,  # 30 seconds in nanoseconds
                'timeout': 5 * 1000000000,    # 5 seconds in nanoseconds
                'retries': healthcheck_retries,
                'start_period': healthcheck_start_period * 1000000000  # 30 seconds in nanoseconds before health check starts
            }
        )
        self.wait_until_healthy('redis', healthcheck_start_period, healthcheck_interval, healthcheck_retries)

        healthcheck_start_period = 60
        healthcheck_interval = 30
        healthcheck_retries = 20
        self.client.services.create(
            name="superset",
            image="ghcr.io/szachovy/superset-cluster-service:latest",
            networks=["superset-network"],
            secrets = [
                docker.types.SecretReference(secret_id=superset_secret_key_id, secret_name="superset_secret_key"),
                docker.types.SecretReference(secret_id=mysql_superset_password_id, secret_name="mysql_superset_password")
            ],
            maxreplicas=1,
            env=[f"VIRTUAL_IP_ADDRESS={virtual_ip_address}"],
            endpoint_spec=docker.types.EndpointSpec(
                mode='vip',
                ports={443: 443}
            ),
            healthcheck = {
                'test': ["CMD", "curl", "-f", "http://localhost:8088/health"],
                'interval': healthcheck_interval * 1000000000,
                'timeout': 5 * 1000000000,
                'retries': healthcheck_retries,
                'start_period': healthcheck_start_period * 1000000000
            },
            mounts=[
                docker.types.Mount(
                    target="/etc/ssl/certs/superset_cluster_certificate.pem",
                    source="/opt/superset-cluster/superset/superset_cluster_certificate.pem",
                    type="bind"
                ),
                docker.types.Mount(
                    target="/etc/ssl/certs/superset_cluster_key.pem",
                    source="/opt/superset-cluster/superset/superset_cluster_key.pem",
                    type="bind"
                )
            ]
        )
        self.wait_until_healthy('superset', healthcheck_start_period, healthcheck_interval, healthcheck_retries)

