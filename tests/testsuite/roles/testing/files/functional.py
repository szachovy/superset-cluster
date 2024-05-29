import json
import re

import ast
import redis
import docker
import requests

# redis_host = '<redis_host>'
# redis_port = <redis_port>

MYSQL_ROOT_PASSWORD='mysql'
NODE_PREFIX='node'
NODES=5

REDIS_HOSTNAME='redis'
REDIS_PORT=6379

CELERY_SQL_LAB_TASK_ANNOTATIONS='sql_lab.get_sql_results'

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
    def extract_session_cookie(request_output: str) -> str:
        return re.search(r'Set-Cookie: session=(.*?);', request_output).group(1)
    
    @staticmethod
    def decode_command_output(command: bytes) -> dict:
        try:
            return ast.literal_eval(command.decode('utf-8'))
        except ValueError:
            return json.loads(command.decode('utf-8'))


class Redis(BaseContainerConnection):
    def __init__(self) -> None:
        super().__init__()
        self.node = 'node-4'

    def status(self) -> bool | ConnectionError:
        test_connection: bytes = self.run_command_on_the_container(f"docker exec {self.get_container_name()} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).ping())'")
        if self.find_in_the_output(test_connection, b'True'):
            return True
        raise ConnectionError('asd')

    def fetch_query_result(self, results_key: float):
        query_result: bytes = self.run_command_on_the_container(f"docker exec {self.get_container_name()} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).get(\"{results_key}\"))'")
        if self.find_in_the_output(query_result, b"None"):
            raise Exception
        return True

class Celery(BaseContainerConnection):
    def __init__(self) -> None:
        super().__init__()
        self.broker: str = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0"
        self.node = 'node-4'
    
    def status(self) -> bool | ConnectionError:
        test_connection: bytes = self.run_command_on_the_container(f"docker exec {self.get_container_name()} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.broker}\").control.inspect().ping())'")
        if self.find_in_the_output(test_connection, b"{'ok': 'pong'}"):
            return True
        raise ConnectionError('asd')

    def find_processed_queries(self):
        celery_workers_stats: dict = self.decode_command_output(
            self.run_command_on_the_container(f"docker exec {self.get_container_name()} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.broker}\").control.inspect().stats())'")
        )
        celery_worker_id: str = next(iter(celery_workers_stats))
        if celery_workers_stats[celery_worker_id]['total'][CELERY_SQL_LAB_TASK_ANNOTATIONS] == 0:
            raise Exception
        return True

    def check_cache(self):
        celery_workers_configuration: dict = self.decode_command_output(
            self.run_command_on_the_container(f"docker exec {self.get_container_name()} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.broker}\").control.inspect().conf())'")
        )
        celery_worker_id: str = next(iter(celery_workers_configuration))
        if all(features in celery_workers_configuration[celery_worker_id]['include'] for features in ['superset.tasks.cache', 'superset.tasks.scheduler']):
            return True    
        raise Exception

class SupersetNodeFunctionalTests(BaseContainerConnection):
    def __init__(self, node: str) -> None:
        super().__init__()
        self.node: str = node
        self._api_default_url: str = "http://localhost:8088/api/v1"
        self._api_authorization_header: str = f"Authorization: Bearer {self._login_to_superset_api()}"
        
        a = self._login_to_superset()
        self._api_csrf_header: str = f"X-CSRFToken: {a['csrf_token']}"
        self._api_session_header: str = f"Cookie: session={a['session_token']}"

        self.redis = Redis()
        self.celery = Celery()

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
        assert json.loads(dashboard_charts.decode('utf-8')).get("result")["charts"] != [], 'err'
        assert json.loads(dashboard_datasets.decode('utf-8')).get("result") != [], 'err'

    def database_status(self) -> bool | ConnectionError:
        payload: str = '{"database_name": "MySQL","sqlalchemy_uri": "mysql+mysqlconnector://root:mysql@172.18.0.2:6446/superset","impersonate_user": false}'
        test_database_connection: bytes = self.run_command_on_the_container(f"curl --silent http://localhost:8088/api/v1/database/test_connection/ --header '{self._api_authorization_header}' --header '{self._api_csrf_header}' --header '{self._api_session_header}' --header 'Content-Type: application/json' --data '{payload}'")
        if self.find_in_the_output(test_database_connection, b'{"message":"OK"}'):
            return True
        raise ConnectionError('asd')

    def run_query(self) -> float | Exception:
        if self.database_status() and self.redis.status() and self.celery.status():
            payload: str = '{"database_id":2,"runAsync":true,"sql":"SELECT * FROM superset.logs;"}'
            sqllab_run_query: bytes = self.run_command_on_the_container(f"curl --silent http://localhost:8088/api/v1/sqllab/execute/ --header 'Content-Type: application/json' --header '{self._api_session_header}' --header '{self._api_csrf_header}' --data '{payload}'")
            dttm_time_query_identifier: float = json.loads(sqllab_run_query.decode('utf-8')).get("query").get("startDttm")
            return dttm_time_query_identifier
        raise Exception
    
    def get_query_results(self, dttm_time_query_identifier: float):        
        import time
        time.sleep(1)
        query_result: dict = self.decode_command_output(
            self.run_command_on_the_container(f"curl --silent 'http://localhost:8088/api/v1/query/updated_since?q=(last_updated_ms:{dttm_time_query_identifier})' --header 'Accept: application/json' --header '{self._api_session_header}' --header '{self._api_csrf_header}'")
        )
        if query_result.get("result")[0]['state'] == 'success':
            results_key: str = f"superset_results{query_result.get('result')[0]['resultsKey']}"
            if self.redis.fetch_query_result(results_key) and self.celery.find_processed_queries() and self.celery.check_cache():
                return True
            raise Exception('vef')
        raise Exception('adwedde')

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
# s.database_status()
dttm = s.run_query()
s.get_query_results(dttm)

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

