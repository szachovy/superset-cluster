
import ast
import ctypes
import ctypes.util
import functools
import re
import threading
import typing

import docker
import requests

class socket_address(ctypes.Structure):
    _fields_ = [
        ('socket_address_family', ctypes.c_ushort),
        ('socket_address_code', ctypes.c_byte * 14)
    ]


class socket_interface(ctypes.Structure):
    _fields_ = [
        ('socket_interface_family', ctypes.c_ushort),
        ('socket_interface_port', ctypes.c_uint16),
        ('socket_interface_address', ctypes.c_byte * 4)
    ]


class network_interface(ctypes.Structure):
    pass


class Overlay(type):
    def __call__(cls, *args, **kwargs) -> typing.Any:
        instance = super().__call__(*args, **kwargs)
        for class_attribute in dir(instance):
            if class_attribute.startswith('_'):
                continue
            attribute = getattr(instance, class_attribute)
            if callable(attribute) and getattr(attribute, '_is_post_init_hook', False):
                attribute()
        return instance

    @staticmethod
    def post_init_hook(method: typing.Callable) -> typing.Callable:
        method._is_post_init_hook = True
        @functools.wraps(method)
        def method_wrapper(self, *args, **kwargs) -> typing.Callable:
            return method(self, *args, **kwargs)
        return method_wrapper

    @staticmethod
    def single_login(method_reference: typing.Callable) -> typing.Callable:
        lock = threading.Lock()
        @functools.wraps(method_reference)
        def method_wrapper(*args, **kwargs) -> str | dict[str, str]:
            if not method_wrapper.object_created:
                with lock:
                    if not method_wrapper.object_created:
                        method_wrapper.tokens = method_reference(*args, **kwargs)
                        method_wrapper.object_created = True
            return method_wrapper.tokens
        method_wrapper.object_created = False
        return method_wrapper


class ContainerUtilities:
    def __init__(self, node: str) -> None:
        self.client: docker.client.DockerClient = docker.from_env()
        self.node: str = node

    def run_command_on_the_container(self, command: str) -> bytes | requests.exceptions.RequestException:
        try:
            request: docker.models.containers.ExecResult = self.client.containers.get(self.node).exec_run(command, stdout=True, stderr=True)
        except (docker.errors.NotFound, docker.errors.APIError) as error:
            raise requests.exceptions.RequestException(f'Can not running commands on the container {self.node}: {error}')
        if request.exit_code != 0:
            raise requests.exceptions.RequestException(f'Command: {command} failed with exit code [{request.exit_code}] giving the following output: {request.output}')
        return request.output

    @staticmethod
    def find_in_the_output(output: bytes, text: bytes) -> bool:
        return text in output

    def stop_node(self, node: str) -> None:
        try:
            self.client.containers.get(node).stop()
        except (docker.errors.NotFound, docker.errors.APIError) as error:
            raise requests.exceptions.RequestException(f'Error stopping node {node}: {error}')

    def find_node_ip(self, node: str) -> str:
        try:
            return self.client.containers.get(node).attrs['NetworkSettings']['Networks'][f'{self.arguments.node_prefix}-network']['IPAddress']
        except (docker.errors.NotFound, docker.errors.APIError, KeyError) as error:
            raise requests.exceptions.RequestException(f'Error finding IP for node {node}: {error}')
    
    @staticmethod
    def extract_session_cookie(request_output: bytes) -> str:
        cookie_section: str | None = re.search(r'Set-Cookie: session=(.*?);', request_output.decode('utf-8'))
        if cookie_section:
            return cookie_section.group(1)
        raise ValueError(f'Session cookie in {request_output} has not been found')
    
    @staticmethod
    def decode_command_output(command: bytes) -> dict:
        try:
            return ast.literal_eval(
                command.decode('utf-8')
                .replace('null', 'None')
                .replace('true', 'True')
                .replace('false', 'False')
            )
        except (ValueError, SyntaxError) as error:
            raise ValueError(f'Error decoding command {command} output: {error}')
