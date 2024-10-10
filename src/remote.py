import functools
import io
import logging
import os
import random
import re
import socket
import paramiko
import pathlib
import marshal

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logging.getLogger("paramiko").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class RemoteConnection:
    def __init__(self, node: str) -> None:
        self.node = node
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(hostname=node, username='superset')
        except (paramiko.ssh_exception.SSHException, socket.gaierror):
            self.ssh_config = paramiko.SSHConfig()
            self.ssh_config.parse(open(f'{pathlib.Path.home()}/.ssh/config'))
            try:
                self.ssh_client.connect(hostname=self.node_hostname(), username='superset', key_filename=self.identity_path())
            except KeyError:
                logger.error(f'Unable to connect to {self.node} from the localhost')
        self.sftp_client = self.ssh_client.open_sftp()

    def log_remote_command_execution(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            command = args[1]
            result = func(*args, **kwargs)
            if result['output']:
                logger.info(f"[Node: {getattr(self, 'node', 'UnknownNode')}] Command: {command} - Output:\n{result['output']}")
            if result['error']:
                logger.error(f"[Node: {getattr(self, 'node', 'UnknownNode')}] Command: {command} - Error:\n{result['error']}")
            return result
        return wrapper

    def node_hostname(self) -> str:
        return self.ssh_config.lookup(self.node)['hostname']
    
    def identity_path(self) -> str:
        return self.ssh_config.lookup(self.node)['identityfile'][0]

    @log_remote_command_execution
    def run_python_container_command(self, command: str) -> None:
        nonce: str = f'{self.node}-{random.randrange(1, 4294967296)}'
        with open(f'{os.path.dirname(os.path.abspath(__file__))}/container.py', 'r') as memfile:
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
