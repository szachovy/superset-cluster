
import ast
import ipaddress
import re
import socket

import docker
import requests
import retry


class ContainerUtilities:
    def __init__(self, node: str) -> None:
        self.client: docker.client.DockerClient = docker.from_env()
        self.node: str = node
        self.counter: int = 0

    @retry.retry(tries=60, delay=5)
    def run_command_on_the_container(self, command: str) -> bytes | requests.exceptions.RequestException:
        self.counter += 5
        print(self.counter)
        try:
            request: docker.models.containers.ExecResult = self.client.containers.get(self.node).exec_run(command, stdout=True, stderr=True)
        except (docker.errors.NotFound, docker.errors.APIError) as error:
            raise requests.exceptions.RequestException(f'Can not running commands on the container {self.node}: {error}')
        if request.exit_code != 0:
            raise requests.exceptions.RequestException(f'Command: {command} failed with exit code [{request.exit_code}] giving the following output: {request.output}')
        return request.output
    
    def info(self):
        return self.client.info()

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
