import json
import re

import ast
import typing
import redis
import docker
import requests

MYSQL_USER='root'
MYSQL_ROOT_PASSWORD='mysql'
NODE_PREFIX='node'
NODES=5

REDIS_HOSTNAME='redis'
REDIS_PORT=6379

CELERY_SQL_LAB_TASK_ANNOTATIONS='sql_lab.get_sql_results'
CELERY_BROKER=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0"

SUPERSET_PASSWORD='admin'
SUPERSET_NODE='node-4'
MGMT_NODE='node-0'
SUPERSET_HOSTNAME='superset'
DATABASE_NAME='superset'

class MyConnectionError(ConnectionError):
    """Exception raised for errors in the connection process.

    Attributes:
        message -- explanation of the error
        code -- optional error code
    """

    def __init__(self, message="There was a problem with the connection", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

from functools import wraps

def run_once(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.tokens = f(*args, **kwargs)
            wrapper.has_run = True
        return wrapper.tokens
    wrapper.has_run = False
    return wrapper

class BaseContainerConnection:
    def __init__(self) -> None:
        self.client = docker.from_env()

    def run_command_on_the_container(self, command: str) -> bytes:
        # if self.client.containers.get(self.node).exec_run(command).exit_code == 0:
        # else raise Exceptioon...
        return self.client.containers.get(self.node).exec_run(command).output

    @staticmethod
    def stop_node(self, node: str) -> None:
        self.client.containers.get(node).stop()

    @staticmethod
    def find_in_the_output(output: bytes, text: bytes) -> bool:
        if output.find(text) != -1:
            return True
        return False
    
    @staticmethod
    def extract_session_cookie(request_output: bytes) -> str:
        return re.search(r'Set-Cookie: session=(.*?);', request_output.decode('utf-8')).group(1)
    
    @staticmethod
    def decode_command_output(command: bytes) -> dict:
        # try:
        return ast.literal_eval(command.decode('utf-8'))
        # except ValueError:
        #     return json.loads(command.decode('utf-8'))

class HealthCheck(type):
    def __call__(cls, *args, **kwargs) -> "cls":
        instance = super(HealthCheck, cls).__call__(*args, **kwargs)
        for attr_name in dir(instance):
            if 'status' in attr_name and callable(getattr(instance, attr_name)):
                getattr(instance, attr_name)()
        return instance

class Redis(BaseContainerConnection, metaclass=HealthCheck):
    def connection_status(self) -> None | AssertionError:
        test_connection: bytes = self.run_command_on_the_container(f"docker exec {REDIS_HOSTNAME} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).ping())'")
        assert self.find_in_the_output(test_connection, b'True'), f'The Redis container {REDIS_HOSTNAME} on {SUPERSET_NODE} is not responding or not working properly'

    def fetch_query_result(self, results_key: float) -> None | AssertionError:
        query_result: bytes = self.run_command_on_the_container(f"docker exec {REDIS_HOSTNAME} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).get(\"{results_key}\"))'")
        assert self.find_in_the_output(query_result, b"None"), f'Query results given key {results_key} not found in Redis'

class Celery(BaseContainerConnection, metaclass=HealthCheck):
    def connection_status(self) -> None | AssertionError: 
        test_connection: bytes = self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{CELERY_BROKER}\").control.inspect().ping())'")
        assert self.find_in_the_output(test_connection, b"{'ok': 'pong'}"), f'The Celery process in the {SUPERSET_HOSTNAME} container on {SUPERSET_NODE} is not responding or not working properly'

    def cache_status(self) -> None | AssertionError:
        celery_workers_configuration: dict = self.decode_command_output(
            self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{CELERY_BROKER}\").control.inspect().conf())'")
        )
        celery_worker_id: str = next(iter(celery_workers_configuration))
        assert all(features in celery_workers_configuration[celery_worker_id]['include'] for features in ['superset.tasks.cache', 'superset.tasks.scheduler']), f'Celery cache and scheduler features in the {CELERY_BROKER} not found'

    def find_processed_queries(self) -> None | AssertionError:
        celery_workers_stats: dict = self.decode_command_output(
            self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{CELERY_BROKER}\").control.inspect().stats())'")
        )
        celery_worker_id: str = next(iter(celery_workers_stats))
        assert celery_workers_stats[celery_worker_id]['total'][CELERY_SQL_LAB_TASK_ANNOTATIONS] > 0, f'Executed SQL Lab queries are not processed or registered by Celery on {SUPERSET_NODE}, check the Celery worker process on {SUPERSET_HOSTNAME}'

class SupersetNodeFunctionalTests(BaseContainerConnection):
    def __init__(self, node: str) -> None:
        super().__init__()
        self.node: str = node
        self.api_default_url: str = "http://localhost:8088/api/v1"
        self.api_authorization_header: str = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header: str = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header: str = f"Cookie: session={self.login_to_superset()['session_token']}"
        self.celery = Celery()
        self.redis = Redis()

    @run_once
    def login_to_superset_api(self) -> str | AssertionError:
        headers: str = "Content-Type: application/json"
        payload: str = f'{{"username": "admin", "password": "{SUPERSET_PASSWORD}", "provider": "db", "refresh": true}}'
        api_login_output: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/security/login --header '{headers}' --data '{payload}'")
        assert self.find_in_the_output(api_login_output, b'"message"'), f'Could not log in to the Superset API {api_login_output}'
        return self.decode_command_output(api_login_output).get("access_token")

    @run_once
    def login_to_superset(self) -> dict[str, str] | AssertionError:
        csrf_login_request: bytes = self.run_command_on_the_container(f"curl --include --url {self.api_default_url}/security/csrf_token/ --header '{self.api_authorization_header}'")
        assert self.find_in_the_output(csrf_login_request, b'"msg"'), f'Could not pass login request {csrf_login_request}'
        session_request_cookie: str = self.extract_session_cookie(csrf_login_request)
        csrf_token: str = json.loads(csrf_login_request.decode('utf-8').split('\r\n\r\n')[1]).get("result")
        superset_login_request: bytes = self.run_command_on_the_container(f"curl --include --url 'http://localhost:8088/login/' --header 'Cookie: session={session_request_cookie}' --data 'csrf_token={csrf_token}'")
        assert self.find_in_the_output(superset_login_request, b'Redirecting...'), f'Invalid login request to Superset. Could not get a response from the server. Check if it is possible to log in to the server manually.'
        superset_login_session_cookie: str = self.extract_session_cookie(superset_login_request)
        return {
            "csrf_token": csrf_token,
            "session_token": superset_login_session_cookie
        }

    def database_status(self) -> None | AssertionError:
        payload: str = f'{{"database_name": {DATABASE_NAME}, "sqlalchemy_uri": "mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_ROOT_PASSWORD}@{MGMT_NODE}:6446/{DATABASE_NAME}", "impersonate_user": false}}'
        test_database_connection: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/test_connection/ --header '{self.api_authorization_header}' --header '{self.api_csrf_header}' --header '{self.api_session_header}' --header 'Content-Type: application/json' --data '{payload}'")
        assert self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), f'Could not connect to the {DATABASE_NAME} on {MGMT_NODE} port 6446, the database is either down or not configured according to the given MySQL Alchemy URI'

    def dashboards_status(self) -> None | AssertionError:
        # self.run_command_on_the_container(f"docker exec {self.get_container_name()} superset load_examples")
        dashboard_charts: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1 --header '{self.api_authorization_header}'")
        dashboard_datasets: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1/datasets --header '{self.api_authorization_header}'")
        assert self.find_in_the_output(dashboard_charts, b'{"message":"Not found"}'), f'No dashboards found in the Superset\'s {DATABASE_NAME} database'
        assert self.find_in_the_output(dashboard_datasets, b'{"message":"Not found"}'), f'No datasets found in the Superset\'s {DATABASE_NAME} database'
        assert self.decode_command_output(dashboard_charts).get("result")["charts"] != [], f'Loaded dashboards to the Superset\'s {DATABASE_NAME} have no charts'
        assert self.decode_command_output(dashboard_datasets).get("result") != [], f'Loaded datasets to the Superset\'s {DATABASE_NAME} are empty'

    def swarm_status(self) -> None | AssertionError:
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'The Swarm node has not been activated'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: true'), f'The {SUPERSET_NODE} is supposed to be a Swarm manager, but it is not'
        assert self.find_in_the_output(swarm_status_output, b'Nodes: 3'), 'The Swarm is expected to consist of three nodes in the pool, but the actual number varies.'

    def run_query(self) -> float | AssertionError:
        # check what assertions include
        payload: str = f'{{"database_id":2, "runAsync": true, "sql": "SELECT * FROM {DATABASE_NAME}.logs;"}}'
        sqllab_run_query: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/sqllab/execute/ --header 'Content-Type: application/json' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --data '{payload}'")
        dttm_time_query_identifier: float = self.decode_command_output(sqllab_run_query).get("query").get("startDttm")
        return dttm_time_query_identifier
    
    def get_query_results(self, dttm_time_query_identifier: float):
        # find what assertions include
        import time
        time.sleep(1)
        query_result: dict = self.decode_command_output(
            self.run_command_on_the_container(f"curl --silent '{self.api_default_url}/query/updated_since?q=(last_updated_ms:{dttm_time_query_identifier})' --header 'Accept: application/json' --header '{self.api_session_header}' --header '{self.api_csrf_header}'")
        )
        if query_result.get("result")[0]['state'] == 'success':
            results_key: str = f"superset_results{query_result.get('result')[0]['resultsKey']}"
            assert self.redis.fetch_query_result(results_key), 'asd'
            assert self.celery.find_processed_queries(), 'qwe'


class MgmtNodeFunctionalTests(BaseContainerConnection):
    def __init__(self, node: str) -> None:
        super().__init__()
        self.node: str = node

    def check_mysql_hostname(self):
        pass

    def routers_status(self):
        self.run_command_on_the_container(f"docker exec {self.get_container_name()} mysqlsh --interactive --uri root:{MYSQL_ROOT_PASSWORD}@{self.node}:6446 --execute \"dba.getCluster(\'cluster\').listRouters();\"")

    def cluster_status(self):
        cluster_status_output: bytes = self.run_command_on_the_container(f"docker exec {self.get_container_name()} mysqlsh --interactive --uri root:{MYSQL_ROOT_PASSWORD}@{self.node}:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
        assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), 'edw'
        assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), 'rte'
    
    def swarm_status(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'edw'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: false'), 'rew'

def pipeline():
    pass

s = SupersetNodeFunctionalTests(f"{NODE_PREFIX}-{NODES-1}")
s.dashboards_status()
# s.database_status()
# dttm = s.run_query()
# s.get_query_results(dttm)

# m = MgmtNodeFunctionalTests(f"{NODE_PREFIX}-0")
# m.cluster_status()
# m.routers_available()

# curl -X POST "http://localhost:8092/api/v1/security/login" -H "Content-Type: application/json" -d f'{"username": "admin", "password": "{SUPERSET_PASSWORD}", "provider": "db", "refresh": true}'
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

if __name__ == '__main__':
    pipeline()
    BaseContainerConnection.stop_node('node-1')
    pipeline()
