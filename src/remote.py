import io
import os
import random
import stat
import paramiko
import pathlib
import marshal

class Remote:
    def __init__(self, node: str) -> None:
        self.node = node
        self.ssh_client = paramiko.SSHClient()
        self.ssh_config = paramiko.SSHConfig()
        self.ssh_config.parse(open(f'{pathlib.Path.home()}/.ssh/config'))
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(hostname=self.node_hostname(), username='superset', key_filename=self.identity_path())
        self.sftp_client = self.ssh_client.open_sftp()

    def node_hostname(self):
        return self.ssh_config.lookup(self.node)['hostname']
    
    def identity_path(self):
        print(self.ssh_config.lookup(self.node))
        return self.ssh_config.lookup(self.node)['identityfile'][0]

    def run_command(self, command: str):
        nonce = f'tmp123-{random.randrange(1, 4294967296)}'
        with open(f'{os.path.dirname(os.path.abspath(__file__))}/container_connection.py', 'r') as memfile:
            code_object = compile(memfile.read() + command, filename=nonce, mode="exec")
            pyc_file = io.BytesIO()
            pyc_file.write(b'o\r\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
            marshal.dump(code_object, pyc_file)
            self.upload_file(content=pyc_file.getvalue(), remote_file_path=f'/opt/{nonce}.pyc')
        try:
            _, stdout, stderr = self.ssh_client.exec_command(f"python3 /opt/{nonce}.pyc")
            output = stdout.read().decode()
            print(output)
            error = stderr.read().decode()
            print(error)
            return output
        except Exception as e:
            print(e)

    def upload_directory(self, local_directory_path, remote_directory_path):
        stack = [(local_directory_path, remote_directory_path)]
        try:
            self.sftp_client.mkdir('/opt/superset-cluster')
        except IOError:
            pass
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
    
    def upload_file(self, content, remote_file_path):
        # if isinstance(content, io.BytesIO):
        #     self.sftp_client.putfo(content, remote_file_path)
        # else:
        if isinstance(content, str):
            content = content.encode('utf-8')
        self.sftp_client.putfo(io.BytesIO(content), remote_file_path)
        # self.sftp_client.putfo(content, remote_file_path)
    
    def change_file_permissions_to_root(self, filepath: str):
        try:
            _, stdout, stderr = self.ssh_client.exec_command(f"chmod 600 {filepath}")
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output
        except Exception as e:
            print(e)
# import crypto
# a = crypto.OpenSSL()
# b = a.generate_private_key()
# c = a.generate_csr(b, 'test')
# d = a.generate_certificate(c, 'test')
# controller = Remote('node-0')
# controller.upload_directory(local_directory_path='../services/mysql-server', remote_directory_path='/opt/superset-cluster/mysql-server')
# controller.upload_file(content=b'qwe', remote_file_path='/opt/superset-cluster/mysql-server/mysql_root_password')
# controller.upload_file(content=b'asd', remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_key.pem')
# controller.upload_file(content=b'zxc', remote_file_path='/opt/superset-cluster/mysql-server/superset_cluster_ca_certificate.pem')
# mysql_node_key = self.generate_private_key()
# mysql_node_certificate = self.generate_certificate(mysql_node_key, common_name=f'{node}-mysql-server')        

# a = Remote('node-0')
# # a.load_ssh_config()
# a.run_command('echo "hi"')
# import io
# import marshal
# import time
# import mysql
# source_code = "mysql.MySQL().prepare_node()"
# code_object = compile(source_code, filename="<string>", mode="exec")
# pyc_file = io.BytesIO()
# pyc_file.write(b'\xcb\r\r\n')
# pyc_file.write(int(time.time()).to_bytes(4, byteorder='little'))
# marshal.dump(code_object, pyc_file)
# pyc_file.seek(0)
# pyc_file.read(8)
# exec(marshal.load(pyc_file))

# import io
# import marshal
# import time
# import mysql
# source_code = "mysql.MySQL().prepare_node()"
# code_object = compile(source_code, filename="<string>", mode="exec")
# pyc_file = io.BytesIO()
# pyc_file.write(b'\xcb\r\r\n')
# pyc_file.write(int(time.time()).to_bytes(4, byteorder='little'))
# marshal.dump(code_object, pyc_file)
# pyc_file.seek(0)
# remote_pyc_path = "/tmp/remote_command.pyc"
# with open(remote_pyc_path, 'wb') as remote_file:
#     remote_file.write(pyc_file.read())
