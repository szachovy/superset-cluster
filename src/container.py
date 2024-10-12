"""
Containers Management Module

This module provides a set of classes and functions for managing containerized
services.

Classes:
--------
1. ContainerInstance:
   An abstract base class representing a generic container instance that requires
   health-check configuration. It serves as a blueprint for implementing concrete
   container services with a `run` method for initialization.

2. ContainerConnection:
   Manages connections to specific Docker containers, offering functionalities
   for running commands, copying files, retrieving logs, and checking container
   health. It provides methods to execute commands on containers, transfer files
   to containers, and monitor the container's health status.

3. MySQLServer (nested in `run_mysql_server`):
   Manages the setup and initialization of a MySQL Server instance, including
   configuration of health-check intervals, retries, and environmental variables.

4. MySQLMgmt (nested in `run_mysql_mgmt`):
   Configures and runs a MySQL Management instance that sets up virtual IPs and
   network-related environmental variables required for container orchestration.

5. Redis (nested in `run_superset`):
   Responsible for initializing and setting up a Redis container in a Docker
   Swarm network, which is essential for supporting Superset in clustered
   deployments.

6. Superset (nested in `run_superset`):
   Manages the setup of the Superset service, configuring health checks,
   environment variables, and Docker secrets for secure handling of sensitive data.

Key Functionalities:
--------------------
- Cluster Management:
  Functions for starting, stopping, and managing containers or services
  such as MySQL, Redis, and Superset, designed to run in a cluster setup using
  Docker containers.

- Command Execution on Containers:
  users are allowed to execute shell commands on the target container and retrieve
  the output, handling any errors that occur during execution.

- File Transfer to Containers:
  users are able to package files as a tar archive
  and transfer them into a specified directory in the target container.

- Container Health Checking:
  mechanisms for polling container health until it reaches a defined "healthy" status or
  a timeout occurs are provided.

Usage Example:
--------------
This module is used on behalf of RemoteConnection, because the following is
executed on the remote nodes.
Being on the node it is possible to run the corroutines on the containers directly:

ContainerConnection(container='mysql').run_mysql_server()  # starts mysql container and returns status
print(ContainerConnection(
    container='mysql'
    ).run_command_on_the_container("echo 'Hello World'")
)  # prints Hello World from mysql container
"""

import abc
import ast
import io
import ipaddress
import json
import random
import re
import socket
import tarfile
import os
import time
import typing
import subprocess

import docker
import requests


# pylint: disable=too-few-public-methods
class ContainerInstance(abc.ABC):
    healthcheck_interval: int
    healthcheck_retries: int
    healthcheck_start_period: int

    @abc.abstractmethod
    def run(self):
        pass


class ContainerConnection:
    def __init__(self, container: str | None) -> None:
        self.client = docker.from_env()
        self.container = container

    def run_command_on_the_container(
            self,
            command: str,
            user: str = "superset",
            environment: dict | None = None
            ) -> bytes:
        try:
            request = self.client.containers.get(
                self.container
                ).exec_run(
                command,
                user=user,
                environment={} if not environment else environment,
                stdout=True,
                stderr=True
            )
        except (docker.errors.NotFound, docker.errors.APIError) as error:
            raise requests.exceptions.RequestException(
                f"Cannot run commands on the container {self.container}"
            ) from error
        if request.exit_code != 0:
            raise requests.exceptions.RequestException(
                f"""Command: {command} failed with exit code [{request.exit_code}]
                    giving the following output: {request.output}
                """
            )
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

    def find_node_ip(self, node: str) -> ipaddress.IPv4Address:
        try:
            return ipaddress.IPv4Address(socket.gethostbyname(node))
        except socket.gaierror as socketerror:
            if socketerror.errno == -2:
                raise socket.gaierror(f"Error finding IPv4 for node {node}") from socketerror
            raise ValueError(f"Cannot find host {node} by name") from socketerror

    @staticmethod
    def extract_session_cookie(request_output: bytes) -> str | ValueError:
        cookie_section = re.search(r"Set-Cookie: session=(.*?);", request_output.decode("utf-8"))
        if cookie_section:
            return cookie_section.group(1)
        raise ValueError(f"Session cookie in {request_output!r} has not been found")

    @staticmethod
    def decode_command_output(command: bytes) -> dict[str, dict]:
        try:
            return ast.literal_eval(
                command.decode("utf-8")
                .replace("null", "None")
                .replace("true", "True")
                .replace("false", "False")
            )
        except (ValueError, SyntaxError) as error:
            raise ValueError(f"Error decoding command {command!r}") from error

    def get_logs(self) -> str:
        if self.container == "superset":
            try:
                return self.client.containers.get(
                    self.client.containers.list(
                        filters={"name": "superset"}
                    )[0].name
                ).logs().decode("utf-8")
            except IndexError:
                return "Container superset has not been spawned by the service"
        if self.container == "mysql-mgmt":
            container_log = ""
            for container in self.client.containers.list(all=True, filters={"name": "mysql-mgmt"})[::-1]:
                container_log += self.client.containers.get(container.name).logs().decode("utf-8") + "\n\n"
            return container_log
        return self.client.containers.get(self.container).logs().decode("utf-8")

    def wait_until_healthy(self, cls: typing.Type[ContainerInstance]) -> str:
        cls.run()  # type: ignore[call-arg]
        time.sleep(cls.healthcheck_start_period)
        for _ in range(cls.healthcheck_retries):
            if self.container == "superset":
                if self.client.api.tasks(filters={"service": "superset"})[0]["Status"]["State"] == "running":
                    return f"{self.get_logs()}\nContainer {self.container} is healthy"
            else:
                if self.client.containers.get(self.container).attrs["State"]["Health"]["Status"] == "healthy":
                    return f"{self.get_logs()}\nContainer {self.container} is healthy"
            time.sleep(cls.healthcheck_interval)
        return f"{self.get_logs()}\nTimeout while waiting for {self.container} healthcheck to be healthy"

    def run_mysql_server(self) -> None:
        class MySQLServer(ContainerInstance):
            def __init__(self, client: docker.client.DockerClient, container: str) -> None:
                self.client = client
                self.container = container
                self.healthcheck_start_period = 90
                self.healthcheck_interval = 5
                self.healthcheck_retries = 3

            def run(self) -> None:
                with open(
                    file="/opt/superset-cluster/mysql-server/seccomp.json",
                    mode="r",
                    encoding="utf-8"
                ) as seccomp:
                    seccomp_parsed = json.dumps(json.load(seccomp), separators=(',', ':'))
                self.client.containers.run(
                    "ghcr.io/szachovy/superset-cluster-mysql-server:latest",
                    detach=True,
                    name=self.container,
                    hostname=socket.gethostname(),
                    restart_policy={"Name": "always"},
                    network="host",
                    cap_add=["SYS_NICE"],
                    security_opt=[f"seccomp={seccomp_parsed}"],
                    environment={
                        "MYSQL_INITDB_SKIP_TZINFO": "true",
                        "MYSQL_ROOT_PASSWORD_FILE": "/var/run/mysqld/mysql_root_password",
                        "SERVER_ID": random.randrange(1, 4294967296),
                        "HEALTHCHECK_START_PERIOD": 150
                    },
                    healthcheck={
                        "test": ["CMD", "mysqladmin", "ping"],
                        "interval": self.healthcheck_interval * 1000000000,
                        "timeout": 10 * 1000000000,
                        "retries": self.healthcheck_retries,
                        "start_period": self.healthcheck_start_period * 1000000000
                    },
                    volumes={
                        "/opt/superset-cluster/mysql-server/mysql_root_password": {
                            "bind": "/var/run/mysqld/mysql_root_password"
                        },
                        "/opt/superset-cluster/mysql-server/mysql_server_certificate.pem": {
                            "bind": "/etc/mysql/ssl/mysql_server_certificate.pem"
                        },
                        "/opt/superset-cluster/mysql-server/mysql_server_key.pem": {
                            "bind": "/etc/mysql/ssl/mysql_server_key.pem"
                        },
                        "/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem": {
                            "bind": "/etc/mysql/ssl/superset_cluster_ca_certificate.pem"
                        }
                    }
                )
        # temporary
        import subprocess
        command = 'docker login ghcr.io -u szachovy -p ...'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(self.wait_until_healthy(MySQLServer(self.client, str(self.container))))  # type: ignore[arg-type]

    # pylint: disable=too-many-arguments
    def run_mysql_mgmt(
            self,
            virtual_ip_address: str,
            virtual_network_mask: str,
            virtual_network_interface: str,
            primary_mysql_node: str,
            secondary_first_mysql_node: str,
            secondary_second_mysql_node: str,
            state: str,
            priority: str) -> None:

        class MySQLMgmt(ContainerInstance):
            # pylint: disable=too-many-arguments
            # pylint: disable=too-many-instance-attributes
            def __init__(
                        self,
                        virtual_ip_address: str,
                        virtual_network_mask: str,
                        virtual_network_interface: str,
                        primary_mysql_node: str,
                        secondary_first_mysql_node: str,
                        secondary_second_mysql_node: str,
                        state: str,
                        priority: str
                    ) -> None:
                self.virtual_ip_address = virtual_ip_address
                self.virtual_network_mask = virtual_network_mask
                self.virtual_network_interface = virtual_network_interface
                self.primary_mysql_node = primary_mysql_node
                self.secondary_first_mysql_node = secondary_first_mysql_node
                self.secondary_second_mysql_node = secondary_second_mysql_node
                self.state = state
                self.priority = priority
                self.healthcheck_start_period = 25
                self.healthcheck_interval = 5
                self.healthcheck_retries = 3

            def calculate_virtual_network(self) -> str:
                return str(ipaddress.IPv4Interface(f"{self.virtual_ip_address}/{self.virtual_network_mask}").network)

            def setup_env(self) -> None:
                os.environ["VIRTUAL_IP_ADDRESS"] = self.virtual_ip_address
                os.environ["VIRTUAL_NETWORK_MASK"] = self.virtual_network_mask
                os.environ["VIRTUAL_NETWORK_INTERFACE"] = self.virtual_network_interface
                os.environ["VIRTUAL_NETWORK"] = self.calculate_virtual_network()
                os.environ["PRIMARY_MYSQL_NODE"] = self.primary_mysql_node
                os.environ["SECONDARY_FIRST_MYSQL_NODE"] = self.secondary_first_mysql_node
                os.environ["SECONDARY_SECOND_MYSQL_NODE"] = self.secondary_second_mysql_node
                os.environ["HEALTHCHECK_START_PERIOD"] = str(self.healthcheck_start_period)
                os.environ["HEALTHCHECK_INTERVAL"] = str(self.healthcheck_interval)
                os.environ["HEALTHCHECK_RETRIES"] = str(self.healthcheck_retries)
                os.environ["STATE"] = state
                os.environ["PRIORITY"] = priority

            def run(self) -> None:
                self.setup_env()
                subprocess.run(" \
                    docker \
                      compose \
                        --file \
                          /opt/superset-cluster/mysql-mgmt/docker_compose.yml \
                        up \
                          initcontainer \
                        --quiet-pull \
                    && \
                    docker \
                      compose \
                        --file \
                          /opt/superset-cluster/mysql-mgmt/docker_compose.yml \
                        up \
                          maincontainer \
                        --detach \
                        --quiet-pull",
                    capture_output=True,  # noqa: E128
                    text=True,  # noqa: E128
                    shell=True,  # noqa: E128
                    check=True,  # noqa: E128
                )  # noqa: E124

        # temporary
        import subprocess
        command = 'docker login ghcr.io -u szachovy -p ...'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return print(
            self.wait_until_healthy(
                MySQLMgmt(  # type: ignore[arg-type]
                    virtual_ip_address=virtual_ip_address,
                    virtual_network_mask=virtual_network_mask,
                    virtual_network_interface=virtual_network_interface,
                    primary_mysql_node=primary_mysql_node,
                    secondary_first_mysql_node=secondary_first_mysql_node,
                    secondary_second_mysql_node=secondary_second_mysql_node,
                    state=state,
                    priority=priority
                )
            )
        )

    def run_superset(self, virtual_ip_address: str, superset_secret_key, mysql_superset_password) -> None:
        class Redis(ContainerInstance):
            def __init__(self, client: docker.client.DockerClient, virtual_ip_address: str) -> None:
                self.virtual_ip_address = virtual_ip_address
                self.client = client
                self.healthcheck_start_period = 10
                self.healthcheck_interval = 10
                self.healthcheck_retries = 5

            def initialize_swarm(self) -> None:
                self.client.swarm.init(advertise_addr=self.virtual_ip_address)

            def create_network(self) -> None:
                self.client.networks.create(name='superset-network', driver='overlay', attachable=True)

            def run(self) -> None:
                self.initialize_swarm()
                self.create_network()
                self.client.containers.run(
                    "redis",
                    detach=True,
                    restart_policy={"Name": "always"},
                    name="redis",
                    hostname="redis",
                    network="superset-network",
                    healthcheck={
                        'test': ["CMD", "redis-cli", "ping"],
                        'interval': self.healthcheck_interval * 1000000000,
                        'timeout': 5 * 1000000000,
                        'retries': self.healthcheck_retries,
                        'start_period': self.healthcheck_start_period * 1000000000
                    }
                )

        class Superset(ContainerInstance):
            def __init__(
                    self,
                    client: docker.client.DockerClient,
                    virtual_ip_address: str,
                    superset_secret_key,
                    mysql_superset_password) -> None:
                self.client = client
                self.virtual_ip_address = virtual_ip_address
                self.superset_secret_key = superset_secret_key
                self.mysql_superset_password = mysql_superset_password
                self.healthcheck_start_period = 60
                self.healthcheck_interval = 60
                self.healthcheck_retries = 14

            def create_superset_secret_key_secret(self) -> str:
                return self.client.secrets.create(
                    name="superset_secret_key",
                    data=self.superset_secret_key
                ).id

            def create_mysql_superset_password_secret(self) -> str:
                return self.client.secrets.create(
                    name="mysql_superset_password",
                    data=self.mysql_superset_password
                ).id

            def run(self) -> None:
                self.client.services.create(
                    name="superset",
                    image="ghcr.io/szachovy/superset-cluster-superset-service:latest",
                    networks=["superset-network"],
                    secrets=[
                        docker.types.SecretReference(
                            secret_id=self.create_superset_secret_key_secret(),
                            secret_name="superset_secret_key"
                        ),
                        docker.types.SecretReference(
                            secret_id=self.create_mysql_superset_password_secret(),
                            secret_name="mysql_superset_password"
                        )
                    ],
                    maxreplicas=1,
                    env=[f"VIRTUAL_IP_ADDRESS={self.virtual_ip_address}"],
                    endpoint_spec=docker.types.EndpointSpec(
                        mode="vip",
                        ports={443: 443}
                    ),
                    healthcheck={
                        "test": ["CMD", "curl", "-f", "http://localhost:8088/health"],
                        "interval": self.healthcheck_interval * 1000000000,
                        "timeout": 5 * 1000000000,
                        "retries": self.healthcheck_retries,
                        "start_period": self.healthcheck_start_period * 1000000000
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

        #temporary
        import subprocess
        command = 'docker login ghcr.io -u szachovy -p ...'
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.container = "redis"
        print(
            self.wait_until_healthy(
                Redis(self.client, virtual_ip_address)  # type: ignore[arg-type]
            )
        )
        self.container = "superset"
        print(
            self.wait_until_healthy(
                Superset(
                    self.client,
                    virtual_ip_address,
                    superset_secret_key,
                    mysql_superset_password
                )  # type: ignore[arg-type]
            )
        )
