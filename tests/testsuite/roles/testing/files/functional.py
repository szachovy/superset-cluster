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
        # if self.client.containers.get(self.node).exec_run(command).exit_code == 0:
        # else raise Exceptioon...
        return self.client.containers.get(self.node).exec_run(command).output

    @staticmethod
    def find_in_the_output(output: bytes, text: bytes) -> bool:
        if output.find(text) != -1:
            return True
        return False

    @staticmethod
    def find_key_value_from_bytes():
        pass
    
    @staticmethod
    def extract_session_cookie(request_output: str) -> str:
        return re.search(r'Set-Cookie: session=(.*?);', request_output).group(1)

class SupersetNodeFunctionalTests(BaseContainerConnection):
    def __init__(self, node: str) -> None:
        super().__init__()
        self.node: str = node
        self._api_default_url: str = "http://localhost:8088/api/v1"
        self._api_authorization_header: str = f"Authorization: Bearer {self._login_to_superset_api()}"
        a = self._login_to_superset()
        self._api_csrf_header: str = f"X-CSRFToken: {a['csrf_token']}"
        self._api_session_header: str = f"Cookie: session={a['session_token']}"

    def _login_to_superset_api(self):
        headers: str = "Content-Type: application/json"
        payload: str = '{"username": "admin", "password": "admin", "provider": "db", "refresh": true}'
        api_login_output: bytes = self.run_command_on_the_container(f"curl --silent --url {self._api_default_url}/security/login --header '{headers}' --data '{payload}'")
        if self.find_in_the_output(api_login_output, b'"message"'):
            raise requests.exceptions.RequestException(f'Could not log in to the Superset API {api_login_output}')
        return json.loads(api_login_output.decode('utf-8')).get("access_token")

    def _login_to_superset(self) -> dict[str, str]:
        csrf_login_request: str = self.run_command_on_the_container(f"curl --include --url {self._api_default_url}/security/csrf_token/ --header '{self._api_authorization_header}'").decode('utf-8')
        session_request_cookie: str = re.search(r'Set-Cookie: session=(.*?);', csrf_login_request).group(1)
        csrf_token: str = json.loads(csrf_login_request.split('\r\n\r\n')[1]).get("result")
        superset_login_request: str = self.run_command_on_the_container(f"curl --include --url 'http://localhost:8088/login/' --header 'Cookie: session={session_request_cookie}' --data 'csrf_token={csrf_token}&username=admin&password=admin'").decode('utf-8')
        superset_login_session_cookie: str = re.search(r'Set-Cookie: session=(.*?);', superset_login_request).group(1)
        return {
            "csrf_token": csrf_token,
            "session_token": superset_login_session_cookie
        }

    def dashboards_status(self):
        # self.run_command_on_the_container(f"docker exec {self.get_container_name()} superset load_examples")
        dashboard_charts: bytes = self.run_command_on_the_container(f"curl --silent --url {self._api_default_url}/dashboard/1 --header '{self._api_authorization_header}'")
        dashboard_datasets: bytes = self.run_command_on_the_container(f"curl --silent --url {self._api_default_url}/dashboard/1/datasets --header '{self._api_authorization_header}'")
        print(json.loads(dashboard_charts.decode('utf-8')).get("result")["charts"])
        print(json.loads(dashboard_datasets.decode('utf-8')).get("result"))
        assert json.loads(dashboard_charts.decode('utf-8')).get("result")["charts"] != [], 'err'
        assert json.loads(dashboard_datasets.decode('utf-8')).get("result") != [], 'err'

    def database_status(self):
        payload: str = '{"database_name": "MySQL","sqlalchemy_uri": "mysql+mysqlconnector://root:mysql@172.18.0.2:6446/superset","impersonate_user": false}'
        test_database_connection: bytes = self.run_command_on_the_container(f"curl --silent http://localhost:8088/api/v1/database/test_connection/ --header '{self._api_authorization_header}' --header '{self._api_csrf_header}' --header '{self._api_session_header}' --header 'Content-Type: application/json' --data '{payload}'")
        print(test_database_connection)
        self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), 'edw'
        # csrf = self.csrf()
        # print(self._api_authorization_header)
        # print(csrf)
        # command = f"""curl --url {self._api_default_url}/database/test_connection/ -H '{self._api_authorization_header}' -H 'X-CSRFToken: {csrf}' -H 'Content-Type: application/json' --data '{payload}'"""
        # print(command)
        # test_database_connection: bytes = self.run_command_on_the_container(command)
        # print(test_database_connection)
        # t = self.run_command_on_the_container("""curl 'http://localhost:8088/api/v1/sqllab/execute/'""" +  f""" -H '{self._api_authorization_header}' -H 'X-CSRFToken: {csrf}'""" + """ -H 'Accept: application/json' -H 'Accept-Language: en-US,en' -H 'Connection: keep-alive' -H 'Content-Type: application/json' -H 'Origin: http://localhost:8092' -H 'Referer: http://localhost:8092/sqllab/' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: same-origin' -H 'Sec-Fetch-Site: same-origin' -H 'Sec-GPC: 1' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36' -H 'sec-ch-ua: "Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"' -H 'sec-ch-ua-mobile: ?0' -H 'sec-ch-ua-platform: "Linux"' --data '{"database_id":2,"runAsync":true,"sql":"SELECT * FROM superset.logs;"}'""")
        # print(t)

    def redis_status(self):
        pass

    def celery_status(self):
        pass

    def swarm_status(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'edw'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: true'), 'rew'
        assert self.find_in_the_output(swarm_status_output, b'Nodes: 3'), 'rsa'

class MgmtNodeFunctionalTests(BaseContainerConnection):
    def __init__(self, node: str) -> None:
        super().__init__()
        self.node: str = node

    def routers_available(self):
        self.run_command_on_the_container(f"docker exec {self.get_container_name()} mysqlsh --interactive --uri root:{MYSQL_ROOT_PASSWORD}@{self.node}:6446 --execute \"dba.getCluster(\'cluster\').listRouters();\"")

    def cluster_status(self):
        cluster_status_output: bytes = self.run_command_on_the_container(f"docker exec {self.get_container_name()} mysqlsh --interactive --uri root:{MYSQL_ROOT_PASSWORD}@{self.node}:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
        assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), 'edw'
        assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), 'rte'
    
    def swarm_status(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'edw'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: false'), 'rew'


s = SupersetNodeFunctionalTests(f"{NODE_PREFIX}-{NODES-1}")
# s.dashboards_status()
s.database_status()

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

# curl 'http://localhost:8088/api/v1/database/test_connection/' \
#   -H 'Content-Type: application/json' \
#   -H 'Cookie: session=.eJwljktOBDEMRO-SNQvHdpx4LtNybEcgRozUPbNC3J0glvV5pfouxzrzei-35_nKt3J8RLkVC6Hejdu0UdeSgatHtEXGizABe-A00nCvqsShPKtwS4BJlQRSl-5E0DyCHUdnSO8YbD27KZKioqVB1d2YEzJk-fRAAomyj7yuPP_f1C39OtfxfHzm1zYUmjQezcUNAGonZhOmlATmcBVtw-Jv5v5wu-dmNvjzC8DmQ6Q.Zk3OVw.XgpKZ1GVYHg-3cNmDfA4-IsDC5M' \
#   -H 'X-CSRFToken: IjkwNTY1NDg1YzZjYTAwMDE3MzQ0YTY0M2U2ZTA0NGRjOTY5NThhZGQi.Zk3OVw.NtQU58eUFRfBeehwqNqJfPO_np4' \
#   --data '{"sqlalchemy_uri":"mysql+mysqlconnector://root:mysql@172.18.0.2:6446/superset","database_name":"MySQL","masked_encrypted_extra":""}

# curl 'http://localhost:8092/api/v1/sqllab/execute/' \
#   -H 'Accept: application/json' \
#   -H 'Accept-Language: en-US,en' \
#   -H 'Connection: keep-alive' \
#   -H 'Content-Type: application/json' \
#   -H 'Cookie: session=.eJwljktOBDEMRO-SNQvHdpx4LtNybEcgRozUPbNC3J0glvV5pfouxzrzei-35_nKt3J8RLkVC6Hejdu0UdeSgatHtEXGizABe-A00nCvqsShPKtwS4BJlQRSl-5E0DyCHUdnSO8YbD27KZKioqVB1d2YEzJk-fRAAomyj7yuPP_f1C39OtfxfHzm1zYUmjQezcUNAGonZhOmlATmcBVtw-Jv5v5wu-dmNvjzC8DmQ6Q.Zk3OVw.XgpKZ1GVYHg-3cNmDfA4-IsDC5M' \
#   -H 'Origin: http://localhost:8092' \
#   -H 'Referer: http://localhost:8092/sqllab/' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: same-origin' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'Sec-GPC: 1' \
#   -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36' \
#   -H 'X-CSRFToken: IjkwNTY1NDg1YzZjYTAwMDE3MzQ0YTY0M2U2ZTA0NGRjOTY5NThhZGQi.Zk3OVw.NtQU58eUFRfBeehwqNqJfPO_np4' \
#   -H 'sec-ch-ua: "Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Linux"' \
#   --data '{"database_id":2,"runAsync":true,"sql":"SELECT * FROM superset.logs;"}'
#   --data-raw '{"client_id":"iPD2lRZkN","database_id":2,"json":true,"runAsync":true,"schema":"superset","sql":"SELECT * FROM superset.logs;\n","sql_editor_id":"1","tab":"Untitled Query 1","tmp_table_name":"","select_as_cta":false,"ctas_method":"TABLE","queryLimit":1000,"expand_data":true}' ;

# curl 'http://localhost:8092/api/v1/query/updated_since?q=(last_updated_ms:1716381375000)' \
#   -H 'Accept: application/json' \
#   -H 'Accept-Language: en-US,en' \
#   -H 'Connection: keep-alive' \
#   -H 'Cookie: session=.eJwljktOBDEMRO-SNQvHdpx4LtNybEcgRozUPbNC3J0glvV5pfouxzrzei-35_nKt3J8RLkVC6Hejdu0UdeSgatHtEXGizABe-A00nCvqsShPKtwS4BJlQRSl-5E0DyCHUdnSO8YbD27KZKioqVB1d2YEzJk-fRAAomyj7yuPP_f1C39OtfxfHzm1zYUmjQezcUNAGonZhOmlATmcBVtw-Jv5v5wu-dmNvjzC8DmQ6Q.Zk3OVw.XgpKZ1GVYHg-3cNmDfA4-IsDC5M' \
#   -H 'Referer: http://localhost:8092/sqllab/' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: same-origin' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'Sec-GPC: 1' \
#   -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36' \
#   -H 'X-CSRFToken: IjkwNTY1NDg1YzZjYTAwMDE3MzQ0YTY0M2U2ZTA0NGRjOTY5NThhZGQi.Zk3OVw.NtQU58eUFRfBeehwqNqJfPO_np4' \
#   -H 'sec-ch-ua: "Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Linux"' ;
# curl 'http://localhost:8092/api/v1/query/updated_since?q=(last_updated_ms:1716381785000)' \
#   -H 'Accept: application/json' \
#   -H 'Accept-Language: en-US,en' \
#   -H 'Connection: keep-alive' \
#   -H 'Cookie: session=.eJwljktOBDEMRO-SNQvHdpx4LtNybEcgRozUPbNC3J0glvV5pfouxzrzei-35_nKt3J8RLkVC6Hejdu0UdeSgatHtEXGizABe-A00nCvqsShPKtwS4BJlQRSl-5E0DyCHUdnSO8YbD27KZKioqVB1d2YEzJk-fRAAomyj7yuPP_f1C39OtfxfHzm1zYUmjQezcUNAGonZhOmlATmcBVtw-Jv5v5wu-dmNvjzC8DmQ6Q.Zk3OVw.XgpKZ1GVYHg-3cNmDfA4-IsDC5M' \
#   -H 'Referer: http://localhost:8092/sqllab/' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: same-origin' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'Sec-GPC: 1' \
#   -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36' \
#   -H 'X-CSRFToken: IjkwNTY1NDg1YzZjYTAwMDE3MzQ0YTY0M2U2ZTA0NGRjOTY5NThhZGQi.Zk3OVw.NtQU58eUFRfBeehwqNqJfPO_np4' \
#   -H 'sec-ch-ua: "Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Linux"' ;
# curl 'http://localhost:8092/api/v1/sqllab/results/?q=(key:%27551d6b3c-e4d3-4fdc-99bc-5f511a08bdd9%27,rows:10000)' \
#   -H 'Accept: application/json' \
#   -H 'Accept-Language: en-US,en' \
#   -H 'Connection: keep-alive' \
#   -H 'Cookie: session=.eJwljktOBDEMRO-SNQvHdpx4LtNybEcgRozUPbNC3J0glvV5pfouxzrzei-35_nKt3J8RLkVC6Hejdu0UdeSgatHtEXGizABe-A00nCvqsShPKtwS4BJlQRSl-5E0DyCHUdnSO8YbD27KZKioqVB1d2YEzJk-fRAAomyj7yuPP_f1C39OtfxfHzm1zYUmjQezcUNAGonZhOmlATmcBVtw-Jv5v5wu-dmNvjzC8DmQ6Q.Zk3OVw.XgpKZ1GVYHg-3cNmDfA4-IsDC5M' \
#   -H 'Referer: http://localhost:8092/sqllab/' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: same-origin' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'Sec-GPC: 1' \
#   -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36' \
#   -H 'X-CSRFToken: IjkwNTY1NDg1YzZjYTAwMDE3MzQ0YTY0M2U2ZTA0NGRjOTY5NThhZGQi.Zk3OVw.NtQU58eUFRfBeehwqNqJfPO_np4' \
#   -H 'sec-ch-ua: "Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Linux"' ;
# curl 'http://localhost:8092/tabstateview/1' \
#   -X 'PUT' \
#   -H 'Accept: application/json' \
#   -H 'Accept-Language: en-US,en' \
#   -H 'Connection: keep-alive' \
#   -H 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryAOAQTIbdal4tjhlW' \
#   -H 'Cookie: session=.eJwljktOBDEMRO-SNQvHdpx4LtNybEcgRozUPbNC3J0glvV5pfouxzrzei-35_nKt3J8RLkVC6Hejdu0UdeSgatHtEXGizABe-A00nCvqsShPKtwS4BJlQRSl-5E0DyCHUdnSO8YbD27KZKioqVB1d2YEzJk-fRAAomyj7yuPP_f1C39OtfxfHzm1zYUmjQezcUNAGonZhOmlATmcBVtw-Jv5v5wu-dmNvjzC8DmQ6Q.Zk3OVw.XgpKZ1GVYHg-3cNmDfA4-IsDC5M' \
#   -H 'Origin: http://localhost:8092' \
#   -H 'Referer: http://localhost:8092/sqllab/' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: same-origin' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'Sec-GPC: 1' \
#   -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36' \
#   -H 'X-CSRFToken: IjkwNTY1NDg1YzZjYTAwMDE3MzQ0YTY0M2U2ZTA0NGRjOTY5NThhZGQi.Zk3OVw.NtQU58eUFRfBeehwqNqJfPO_np4' \
#   -H 'sec-ch-ua: "Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Linux"' \
#   --data-raw $'------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="database_id"\r\n\r\n2\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="schema"\r\n\r\n"superset"\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="sql"\r\n\r\n"SELECT * FROM superset.logs;\\n"\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="label"\r\n\r\n"Untitled Query 1"\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="query_limit"\r\n\r\n1000\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="latest_query_id"\r\n\r\n"iPD2lRZkN"\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="hide_left_bar"\r\n\r\nfalse\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="autorun"\r\n\r\nfalse\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW\r\nContent-Disposition: form-data; name="extra_json"\r\n\r\n"{\\"updatedAt\\":1716381789266,\\"version\\":1}"\r\n------WebKitFormBoundaryAOAQTIbdal4tjhlW--\r\n'