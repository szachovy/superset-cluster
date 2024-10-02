import io
import os
import paramiko
import pathlib

class Remote:
    def __init__(self, node: str) -> None:
        self.node = node
        self.ssh_client = paramiko.SSHClient()
        print(self.node_hostname())
        # self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(hostname=self.node_hostname(), username='superset', key_filename='/home/wjmaj/Public/Work/superset-cluster-all/superset-cluster/tests/setup/id_rsa')
        # self.sftp_client = self.ssh_client.open_sftp()

    def node_hostname(self):
        my_config = paramiko.SSHConfig()
        my_config.parse(open(f'{pathlib.Path.home()}/.ssh/config'))
        conf = my_config.lookup(self.node)['hostname']
        return conf

    def run_command(self, command):
        try:
            _, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode()
            print(output)
            error = stderr.read().decode()
            print(error)
        except Exception as e:
            print(e)

    def upload_directory(self, local_directory_path, remote_directory_path):
        stack = [(local_directory_path, remote_directory_path)]
        self.sftp_client.mkdir('/opt/superset-cluster')
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
        self.sftp_client.putfo(io.StringIO(content), remote_file_path)

a = Remote('node-0')
# a.load_ssh_config()
a.run_command('echo "hi"')
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