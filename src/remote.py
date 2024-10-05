import io
import os
import random
import socket
import paramiko
import pathlib
import marshal

class Remote:
    def __init__(self, node: str) -> None:
        self.node = node
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(hostname=node, username='superset')
        except (paramiko.ssh_exception.SSHException, socket.gaierror):
            self.ssh_config = paramiko.SSHConfig()
            self.ssh_config.parse(open(f'{pathlib.Path.home()}/.ssh/config'))
            self.ssh_client.connect(hostname=self.node_hostname(), username='superset', key_filename=self.identity_path())
        self.sftp_client = self.ssh_client.open_sftp()

    def node_hostname(self) -> str:
        return self.ssh_config.lookup(self.node)['hostname']
    
    def identity_path(self) -> str:
        return self.ssh_config.lookup(self.node)['identityfile'][0]

    def run_python_command(self, command: str) -> None:
        nonce: str = f'{self.node}-{random.randrange(1, 4294967296)}'
        with open(f'{os.path.dirname(os.path.abspath(__file__))}/container_connection.py', 'r') as memfile:
            code_object = compile(memfile.read() + command, filename=nonce, mode="exec")
            pyc_file = io.BytesIO()
            pyc_file.write(b'o\r\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            marshal.dump(code_object, pyc_file)
            self.upload_file(content=pyc_file.getvalue(), remote_file_path=f'/opt/{nonce}.pyc')
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(f"python3 /opt/{nonce}.pyc")
            print(stdin)
            output = stdout.read().decode()
            print(output)
            error = stderr.read().decode()
            print(error)
            return output
        except Exception as e:
            print(e)


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
