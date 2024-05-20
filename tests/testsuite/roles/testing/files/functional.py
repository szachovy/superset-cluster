import json
import re

import redis
import docker
import requests

# redis_host = '<redis_host>'
# redis_port = <redis_port>

# try:
#     redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
#     redis_client.ping()
#     print("Connection to Redis successful.")
# except Exception as e:
#     print(f"Error connecting to Redis: {e}")

MYSQL_ROOT_PASSWORD='mysql'
NODE_PREFIX='node'
NODES=5


class BaseContainerConnection:
    def __init__(self) -> None:
        self.client = docker.from_env()

    def get_container_name(self) -> str:
        return self.client.containers.get(self.node).exec_run("docker ps --latest --format {{.Names}}").output.decode('utf-8').replace('\n', '')

    def run_command_on_the_container(self, command: str) -> bytes:
        return self.client.containers.get(self.node).exec_run(command).output

    def find_(self):
        pass

class SupersetNodeFunctionalTests(BaseContainerConnection):
    def __init__(self, node: str) -> None:
        super().__init__()
        self.node: str = node
        self._api_default_url: str = "http://localhost:8088/api/v1"
        self._api_default_header: str = f"Authorization: Bearer {self._login_to_superset_api()}"

    def _login_to_superset_api(self):
        headers: str = "Content-Type: application/json"
        payload: str = '{"username": "admin", "password": "admi", "provider": "db", "refresh": true}'
        api_login_output: bytes = self.run_command_on_the_container(f"curl --silent --request POST --url {self._api_default_url}/security/login --header '{headers}' --data '{payload}'")
        print(api_login_output)
        # if self.find_(api_login_output, "message"):
        #   raise requests.exceptions.RequestException()
        # return json.loads(api_login_output.decode('utf-8')).get("access_token")

        # api_login = requests.post(f"{self._api_default_url}/security/login",
        #                           headers=headers,
        #                           data=json.dumps(payload))
        # api_login.raise_for_status()
        # return api_login.json().get("access_token")

    def dashboards_status(self):
        # self.run_command_on_the_container(f"docker exec {self.get_container_name()} superset load_examples")
        # print(self._api_default_header)
        dashboard_charts = requests.get(f"{self._api_default_url}/dashboard/1", headers=self._api_default_header)
        dashboard_datasets = requests.get(f"{self._api_default_url}/dashboard/1/datasets", headers=self._api_default_header)
        assert dashboard_charts.json().get("result")["charts"] != [], 'err'
        assert dashboard_datasets.json().get("result") != [], 'err'

    def database_status(self):
        pass

    def redis_status(self):
        pass

    def celery_status(self):
        pass

    def swarm_status(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert swarm_status_output.find(b'Swarm: active') != -1, 'edw'
        assert swarm_status_output.find(b'Is Manager: true') != -1, 'rew'
        assert swarm_status_output.find(b'Nodes: 3') != -1, 'rsa'

class MgmtNodeFunctionalTests(BaseContainerConnection):
    def __init__(self, node: str) -> None:
        super().__init__()
        self.node: str = node

    def routers_available(self):
        self.run_command_on_the_container(f"docker exec {self.get_container_name()} mysqlsh --interactive --uri root:{MYSQL_ROOT_PASSWORD}@{self.node}:6446 --execute \"dba.getCluster(\'cluster\').listRouters();\"")

    def cluster_status(self):
        cluster_status_output: bytes = self.run_command_on_the_container(f"docker exec {self.get_container_name()} mysqlsh --interactive --uri root:{MYSQL_ROOT_PASSWORD}@{self.node}:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
        assert cluster_status_output.find(b'"status": "OK"') != -1, 'edw'
        assert cluster_status_output.find(b'"topologyMode": "Single-Primary"') != -1, 'rte'
    
    def swarm_status(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert swarm_status_output.find(b'Swarm: active') != -1, 'edw'
        assert swarm_status_output.find(b'Is Manager: false') != -1, 'rew'


s = SupersetNodeFunctionalTests(f"{NODE_PREFIX}-{NODES-1}")
# s.dashboards_status()

# m = MgmtNodeFunctionalTests(f"{NODE_PREFIX}-0")
# m.cluster_status()
# m.routers_available()

# curl -X POST "http://localhost:8092/api/v1/security/login" -H "Content-Type: application/json" -d '{"username": "admin", "password": "admin", "provider": "db", "refresh": true}'
# curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" "http://YOUR_SUPERSET_INSTANCE/api/v1/dashboard/"
# print(s.connect_to_container('node-0').exec_run('env'))
# print(s.cluster_status())
# client = docker.from_env()
# containers = client.containers.get("node-0").exec_run("docker ps --latest --format {{.Names}}").output.decode('utf-8').replace('\n', '')
# print(containers)
# primary_node_ip: str = 'node-0'
# a = client.containers.get("node-0").exec_run("docker exec mysql-mgmt mysqlsh --interactive --uri root:mysql@node-0:6446 --execute \"dba.getCluster(\'cluster\').status();\"").output
# print(a)
# print(type(a))
# docker exec mysql-mgmt mysqlsh --json --interactive --uri root:mysql@node-0:6446 --execute "dba.getCluster('cluster').status();"