
import json
import re

import ast
import typing
import docker
import requests
import functools


MYSQL_USER='root'
MYSQL_PASSWORD='mysql'
NODE_PREFIX='node'
NODES=5

REDIS_HOSTNAME='redis'
REDIS_PORT=6379

CELERY_SQL_LAB_TASK_ANNOTATIONS='sql_lab.get_sql_results'
CELERY_BROKER=f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0"

SUPERSET_PASSWORD='admin'
SUPERSET_NODE='node-4'
MGMT_PRIMARY_NODE='node-0'
MYSQL_PRIMARY_NODE='node-1'
MYSQL_SECONDARY_NODES=['node-2', 'node-3']
SUPERSET_HOSTNAME='superset'
DATABASE_NAME='superset'


class BaseNodeConnection:
    def __init__(self, node: str | None = None) -> None:
        self.client: docker.client.DockerClient = docker.from_env()
        self.node: str = node

    def run_command_on_the_container(self, command: str) -> bytes | requests.exceptions.RequestException:
        request: docker.models.containers.ExecResult = self.client.containers.get(self.node).exec_run(command)
        if request.exit_code != 0:
            raise requests.exceptions.RequestException(f'Command: {command} failed with exit code [{request.exit_code}] giving the following output: {request.output}')
        return request.output

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

class Utils:
    def singleton_function(function_reference: typing.Callable) -> typing.Callable:
        @functools.wraps(function_reference)
        def wrapper(*args, **kwargs) -> str | dict[str, str]:
            if not wrapper.object_created:
                wrapper.tokens = function_reference(*args, **kwargs)
                wrapper.object_created = True
            return wrapper.tokens
        wrapper.object_created = False
        return wrapper

    def post_init_hook(self):
        for name in dir(self):
            attr = getattr(self, name)
            if callable(attr) and getattr(attr, '_is_post_init_hook', False):
                attr()

class Redis(BaseNodeConnection):
    def connection_status(self) -> None | AssertionError:
        test_connection: bytes = self.run_command_on_the_container(f"docker exec {REDIS_HOSTNAME} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).ping())'")
        assert self.find_in_the_output(test_connection, b'True'), f'The Redis container {REDIS_HOSTNAME} on {SUPERSET_NODE} is not responding or not working properly'

    def fetch_query_result(self, results_key: float) -> None | AssertionError:
        query_result: bytes = self.run_command_on_the_container(f"docker exec {REDIS_HOSTNAME} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).get(\"{results_key}\"))'")
        assert self.find_in_the_output(query_result, b"None"), f'Query results given key {results_key} not found in Redis'


class Celery(BaseNodeConnection):
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


class SupersetNodeFunctionalTests(BaseNodeConnection):
    def __init__(self) -> None:
        super().__init__(node=SUPERSET_NODE)
        self.api_default_url: str = "http://localhost:8088/api/v1"
        self.api_authorization_header: str = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header: str = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header: str = f"Cookie: session={self.login_to_superset()['session_token']}"
        self.celery = Celery()
        self.redis = Redis()
        print(type(self.celery))
        print(type(self.redis))

    @Utils.singleton_function
    def login_to_superset_api(self) -> str | AssertionError:
        headers: str = "Content-Type: application/json"
        payload: str = f'{{"username": "admin", "password": "{SUPERSET_PASSWORD}", "provider": "db", "refresh": true}}'
        api_login_output: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/security/login --header '{headers}' --data '{payload}'")
        assert not self.find_in_the_output(api_login_output, b'"message"'), f'Could not log in to the Superset API {api_login_output}'
        return self.decode_command_output(api_login_output).get("access_token")

    @Utils.singleton_function
    def login_to_superset(self) -> dict[str, str] | AssertionError:
        csrf_login_request: bytes = self.run_command_on_the_container(f"curl --include --url {self.api_default_url}/security/csrf_token/ --header '{self.api_authorization_header}'")
        assert not self.find_in_the_output(csrf_login_request, b'"msg"'), f'Could not pass login request {csrf_login_request}'
        session_request_cookie: str = self.extract_session_cookie(csrf_login_request)
        csrf_token: str = json.loads(csrf_login_request.decode('utf-8').split('\r\n\r\n')[1]).get("result")
        superset_login_request: bytes = self.run_command_on_the_container(f"curl --include --url 'http://localhost:8088/login/' --header 'Cookie: session={session_request_cookie}' --data 'csrf_token={csrf_token}'")
        assert not self.find_in_the_output(superset_login_request, b'Redirecting...'), f'Invalid login request to Superset. Could not get a response from the server. Check if it is possible to log in to the server manually.'
        superset_login_session_cookie: str = self.extract_session_cookie(superset_login_request)
        return {
            "csrf_token": csrf_token,
            "session_token": superset_login_session_cookie
        }

    def database_status(self) -> None | AssertionError:
        payload: str = f'{{"database_name": {DATABASE_NAME}, "sqlalchemy_uri": "mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MGMT_PRIMARY_NODE}:6446/{DATABASE_NAME}", "impersonate_user": false}}'
        test_database_connection: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/test_connection/ --header '{self.api_authorization_header}' --header '{self.api_csrf_header}' --header '{self.api_session_header}' --header 'Content-Type: application/json' --data '{payload}'")
        assert self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), f'Could not connect to the {DATABASE_NAME} on {MGMT_PRIMARY_NODE} port 6446, the database is either down or not configured according to the given MySQL Alchemy URI'

    def dashboards_status(self) -> None | AssertionError:
        # self.run_command_on_the_container(f"docker exec {self.get_container_name()} superset load_examples")
        dashboard_charts: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1 --header '{self.api_authorization_header}'")
        dashboard_datasets: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1/datasets --header '{self.api_authorization_header}'")
        assert not self.find_in_the_output(dashboard_charts, b'{"message":"Not found"}'), f'No dashboards found in the Superset\'s {DATABASE_NAME} database'
        assert not self.find_in_the_output(dashboard_datasets, b'{"message":"Not found"}'), f'No datasets found in the Superset\'s {DATABASE_NAME} database'
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


class MgmtNodeFunctionalTests(BaseNodeConnection):
    def __init__(self) -> None:
        super().__init__(node=MGMT_PRIMARY_NODE)

    def routers_status(self):
        # find asserts
        self.run_command_on_the_container(f"docker exec {MGMT_PRIMARY_NODE} mysqlsh --interactive --uri {MYSQL_USER}:{MYSQL_PASSWORD}@{MGMT_PRIMARY_NODE}:6446 --execute \"dba.getCluster(\'cluster\').listRouters();\"")

    def cluster_status(self):
        cluster_status_output: bytes = self.run_command_on_the_container(f"docker exec {MGMT_PRIMARY_NODE} mysqlsh --interactive --uri root:{MYSQL_PASSWORD}@{MGMT_PRIMARY_NODE}:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
        assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), 'edw'
        assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), 'rte'

    def swarm_status(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'edw'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: false'), 'rew'

    def check_mysql_after_disaster(self):
        # SELECT @@hostname; == ...
        # self.stop_node(MYSQL_PRIMARY_NODE)
        # SELECT @@hostname; == ...
        pass

    def check_router_after_disaster(self):
        # self.stop_node(MGMT_PRIMARY_NODE)
        pass


if __name__ == '__main__':
    s = SupersetNodeFunctionalTests()
    # s.dashboards_status()
    # s.database_status()
    # dttm = s.run_query()
    # s.get_query_results(dttm)