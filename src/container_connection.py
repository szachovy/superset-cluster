
import ast
import io
import ipaddress
import json
import random
import re
import socket
import tarfile
import os

import docker
import requests


class ContainerUtilities:
    def __init__(self, container: str | None) -> None:
        self.client: docker.client.DockerClient = docker.from_env()
        self.container: str = container

    def run_command_on_the_container(self, command: str) -> bytes | requests.exceptions.RequestException:
        try:
            request: docker.models.containers.ExecResult = self.client.containers.get(self.container).exec_run(command, stdout=True, stderr=True)
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

    def start(self):
        if self.container == 'mysql':
            self.run_mysql_server()
        elif self.container == 'mysql-mgmt':
            self.run_mysql_mgmt()
        elif self.container == 'redis':
            self.run_redis()
        elif self.container == 'superset':
            self.run_superset()

    def run_mysql_server(self):
        # temporary
        import subprocess
        command = f'docker login ghcr.io -u szachovy -p ...'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                    "HEALTHCHECK_START_PERIOD": 90
                },
                healthcheck = {
                    'test': ['CMD', 'mysqladmin', 'ping'],
                    'interval': 5 * 1000000000,
                    'timeout': 10 * 1000000000,
                    'retries': 3,
                    'start_period': 90 * 1000000000
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

    def run_mysql_mgmt():
        pass

    def run_redis():
        pass

    def run_superset():
        pass

