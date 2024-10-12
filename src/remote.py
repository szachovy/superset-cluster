"""
Remote Connection Management Module

This module facilitates operations to the superset-cluster nodes.

Classes:
--------
- `RemoteConnection`:
  This class manages secure remote connections to the specified remote node using SSH and SFTP.
  It allows for executing commands on remote servers, uploading files and directories,
  and managing cryptographic keys and certificates for secure communications.

Key Functionalities:
--------------------
- SSH and SFTP client connection: Establishes SSH and SFTP connection though system settings or user's SSH config file.

- Runs remote python commands: Logs and executes a Python command on the remote node via
  compiled container.py python file placement with functions to run on it.

- Remote filesystem management: Sets permissions, creates, and uploads files or directories to the remote paths
  using dedicated SFTP client routines.

Example Usage:
--------------
To create a connection to a remote node, instantiate the RemoteConnection class with the node's
hostname. After the connection is established, you can use its methods to interact
with the remote server.

```python
remote_node = RemoteConnection("mysql1")
remote_node.create_directory("/opt/example")
remote_node.upload_directory(".", "/opt/example/content")
remote_node.upload_file("/opt/example/content/run.py")
output = remote_node.run_python_container_command("print('Hello World')")
print(output)
remote_node.change_permissions_to_root("/opt/example/content/run.py")
"""

import functools
import io
import logging
import marshal
import os
import pathlib
import random
import socket
import typing

import cryptography
import paramiko

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logging.getLogger("paramiko").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class RemoteConnection:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, node: str) -> None:
        self.node = node
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(hostname=node, username='superset')
        except (paramiko.ssh_exception.SSHException, socket.gaierror):
            self.ssh_config = paramiko.SSHConfig()
            with open(
                file=f"{pathlib.Path.home()}/.ssh/config",
                mode="r",
                encoding="utf-8"
            ) as ssh_config_file:
                self.ssh_config.parse(ssh_config_file)
            try:
                self.ssh_client.connect(
                    hostname=self.node_hostname(),
                    username='superset',
                    key_filename=self.identity_path()
                )
            except KeyError:
                logger.error("Unable to connect to %s from the localhost", self.node)
        self.sftp_client = self.ssh_client.open_sftp()
        self.key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey | None = None
        self.csr: cryptography.x509.base.CertificateSigningRequest | None = None
        self.certificate: cryptography.x509.base.Certificate | None = None
        self.superset_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey | None = None
        self.superset_csr: cryptography.x509.base.CertificateSigningRequest | None = None
        self.superset_certificate: cryptography.x509.base.Certificate | None = None

    @staticmethod
    def log_remote_command_execution(func: typing.Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            command = args[1]
            result = func(*args, **kwargs)
            if result["output"]:
                logger.info(
                    "[Node: %s] Command: %s - Output:\n%s",
                    getattr(self, 'node', 'UnknownNode'),
                    command,
                    result["output"]
                )
            if result["error"]:
                logger.error(
                    "[Node: %s] Command: %s - Error:\n%s",
                    getattr(self, "node", "UnknownNode"),
                    command,
                    result["error"]
                )
            return result
        return wrapper

    def node_hostname(self) -> str:
        return self.ssh_config.lookup(self.node)['hostname']

    def identity_path(self) -> str:
        return self.ssh_config.lookup(self.node)['identityfile'][0]

    @log_remote_command_execution
    def run_python_container_command(self, command: str) -> dict:
        nonce = f'{self.node}-{random.randrange(1, 4294967296)}'
        with open(
            file=f"{os.path.dirname(os.path.abspath(__file__))}/container.py",
            mode="r",
            encoding="utf-8"
        ) as memfile:
            code_object = compile(memfile.read() + command, filename=nonce, mode="exec")
            pyc_file = io.BytesIO()
            pyc_file.write(b'o\r\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            marshal.dump(code_object, pyc_file)
            self.upload_file(content=pyc_file.getvalue(), remote_file_path=f'/opt/{nonce}.pyc')
        _, stdout, stderr = self.ssh_client.exec_command(f"python3 /opt/{nonce}.pyc")
        return {
            "output": stdout.read().decode(),
            "error": stderr.read().decode()
        }

    def upload_directory(self, local_directory_path: str, remote_directory_path: str) -> None:
        stack = [(local_directory_path, remote_directory_path)]
        while stack:
            local_path, remote_path = stack.pop()
            try:
                self.sftp_client.mkdir(remote_path)
            except IOError:
                pass
            for item in os.listdir(local_path):
                local_item_path = os.path.join(local_path, item)
                remote_item_path = os.path.join(remote_path, item)
                if os.path.isdir(local_item_path):
                    stack.append((local_item_path, remote_item_path))
                else:
                    self.sftp_client.put(local_item_path, remote_item_path)

    def create_directory(self, remote_directory_path: str) -> None:
        self.sftp_client.mkdir(remote_directory_path)

    def upload_file(self, content: str | bytes, remote_file_path: str) -> None:
        if isinstance(content, str):
            content = content.encode('utf-8')
        self.sftp_client.putfo(io.BytesIO(content), remote_file_path)

    def change_permissions_to_root(self, filepath: str) -> None:
        self.ssh_client.exec_command(f"chmod 600 {filepath}")
