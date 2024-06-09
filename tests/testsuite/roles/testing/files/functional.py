
import ast
import functools
import json
import re
import threading
import time
import typing

import docker
import requests


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
MGMT_HOSTNAME='mysql-mgmt'
MYSQL_PRIMARY_NODE='node-1'
MYSQL_SECONDARY_NODES=['node-2', 'node-3']
SUPERSET_HOSTNAME='superset'
DATABASE_NAME='superset'


_MYSQL_NODE_DISASTER_DELAY=330
_MGMT_NODE_DISASTER_DELAY=12

class BaseNodeConnection:
    def __init__(self, node: str) -> None:
        self.client: docker.client.DockerClient = docker.from_env()
        self.node: str = node

    def run_command_on_the_container(self, command: str) -> bytes | requests.exceptions.RequestException:
        try:
            request: docker.models.containers.ExecResult = self.client.containers.get(self.node).exec_run(command)
        except (docker.errors.NotFound, docker.errors.APIError) as error:
            raise requests.exceptions.RequestException(f'Can not running commands on the container {self.node}: {error}')
        if request.exit_code != 0:
            raise requests.exceptions.RequestException(f'Command: {command} failed with exit code [{request.exit_code}] giving the following output: {request.output}')
        return request.output

    def stop_node(self, node: str) -> None:
        try:
            self.client.containers.get(node).stop()
        except (docker.errors.NotFound, docker.errors.APIError) as error:
            raise requests.exceptions.RequestException(f'Error stopping node {node}: {error}')

    def find_node_ip(self, node: str) -> str:
        try:
            return self.client.containers.get(node).attrs['NetworkSettings']['Networks'][f'{NODE_PREFIX}-network']['IPAddress']
        except (docker.errors.NotFound, docker.errors.APIError, KeyError) as error:
            raise requests.exceptions.RequestException(f'Error finding IP for node {node}: {error}')

    @staticmethod
    def find_in_the_output(output: bytes, text: bytes) -> bool:
        return text in output
    
    @staticmethod
    def extract_session_cookie(request_output: bytes) -> str:
        cookie_section: str | None = re.search(r'Set-Cookie: session=(.*?);', request_output.decode('utf-8'))
        if cookie_section:
            return cookie_section.group(1)
        raise ValueError(f'Session cookie in {request_output} has not been found')
    
    @staticmethod
    def decode_command_output(command: bytes) -> dict:
        try:
            return ast.literal_eval(
                command.decode('utf-8')
                .replace('null', 'None')
                .replace('true', 'True')
                .replace('false', 'False')
            )
        except (ValueError, SyntaxError) as error:
            raise ValueError(f'Error decoding command {command} output: {error}')


class Utils(type):
    def __call__(cls, *args, **kwargs) -> typing.Any:
        instance = super().__call__(*args, **kwargs)
        for class_attribute in dir(instance):
            if class_attribute.startswith('_'):
                continue
            attribute = getattr(instance, class_attribute)
            if callable(attribute) and getattr(attribute, '_is_post_init_hook', False):
                attribute()
        return instance

    @staticmethod
    def post_init_hook(method: typing.Callable) -> typing.Callable:
        method._is_post_init_hook = True
        @functools.wraps(method)
        def method_wrapper(self, *args, **kwargs) -> typing.Callable:
            return method(self, *args, **kwargs)
        return method_wrapper

    @staticmethod
    def singleton_function(method_reference: typing.Callable) -> typing.Callable:
        lock = threading.Lock()
        @functools.wraps(method_reference)
        def method_wrapper(*args, **kwargs) -> str | dict[str, str]:
            if not method_wrapper.object_created:
                with lock:
                    if not method_wrapper.object_created:
                        method_wrapper.tokens = method_reference(*args, **kwargs)
                        method_wrapper.object_created = True
            return method_wrapper.tokens
        method_wrapper.object_created = False
        return method_wrapper


class Redis(BaseNodeConnection, metaclass=Utils):
    def __init__(self) -> None:
        super().__init__(node=SUPERSET_NODE)

    @Utils.post_init_hook
    def status(self) -> None | AssertionError:
        test_connection: bytes = self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).ping())'")
        assert self.find_in_the_output(test_connection, b'True'), f'The Redis container {SUPERSET_HOSTNAME} on {SUPERSET_NODE} is not responding or not working properly'

    def fetch_query_result(self, results_key: float) -> bool | AssertionError:
        query_result: bytes = self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import redis; print(redis.StrictRedis(host=\"{REDIS_HOSTNAME}\", port={REDIS_PORT}).get(\"{results_key}\"))'")
        assert not self.find_in_the_output(query_result, b"None"), f'Query results given key {results_key} not found in Redis'
        return True


class Celery(BaseNodeConnection, metaclass=Utils):
    def __init__(self) -> None:
        super().__init__(node=SUPERSET_NODE)

    @Utils.post_init_hook
    def status(self) -> None | AssertionError: 
        test_connection: bytes = self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{CELERY_BROKER}\").control.inspect().ping())'")
        assert self.find_in_the_output(test_connection, b"{'ok': 'pong'}"), f'The Celery process in the {SUPERSET_HOSTNAME} container on {SUPERSET_NODE} is not responding or not working properly'

    @Utils.post_init_hook
    def status_cache(self) -> None | AssertionError:
        celery_workers_configuration: dict = self.decode_command_output(
            self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{CELERY_BROKER}\").control.inspect().conf())'")
        )
        celery_worker_id: str = next(iter(celery_workers_configuration))
        assert all(features in celery_workers_configuration[celery_worker_id]['include'] for features in ['superset.tasks.cache', 'superset.tasks.scheduler']), f'Celery cache and scheduler features in the {CELERY_BROKER} not found'

    def find_processed_queries(self) -> bool | AssertionError:
        celery_workers_stats: dict = self.decode_command_output(
            self.run_command_on_the_container(f"docker exec {SUPERSET_HOSTNAME} python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{CELERY_BROKER}\").control.inspect().stats())'")
        )
        celery_worker_id: str = next(iter(celery_workers_stats))
        assert celery_workers_stats[celery_worker_id]['total'][CELERY_SQL_LAB_TASK_ANNOTATIONS] > 0, f'Executed SQL Lab queries are not processed or registered by Celery on {SUPERSET_NODE}, check the Celery worker process on {SUPERSET_HOSTNAME}'
        return True


class SupersetNodeFunctionalTests(BaseNodeConnection, metaclass=Utils):
    def __init__(self) -> None:
        super().__init__(node=SUPERSET_NODE)
        self.api_default_url: str = "http://localhost:8088/api/v1"
        self.api_authorization_header: str = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header: str = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header: str = f"Cookie: session={self.login_to_superset()['session_token']}"
        self.celery: typing.Type = Celery()
        self.redis: typing.Type = Redis()

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

    @Utils.post_init_hook
    def status_database(self) -> None | AssertionError:
        payload: str = f'{{"database_name": "MySQL", "sqlalchemy_uri": "mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{self.find_node_ip(MGMT_PRIMARY_NODE)}:6446/{DATABASE_NAME}", "impersonate_user": false}}'
        test_database_connection: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/test_connection/ --header '{self.api_authorization_header}' --header '{self.api_csrf_header}' --header '{self.api_session_header}' --header 'Content-Type: application/json' --data '{payload}'")
        assert self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), f'Could not connect to the {DATABASE_NAME} on {MGMT_PRIMARY_NODE} port 6446, the database is either down or not configured according to the given SQL Alchemy URI'

    @Utils.post_init_hook
    def status_datasets(self) -> None | AssertionError:
        dashboard_charts: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1 --header '{self.api_authorization_header}'")
        dashboard_datasets: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1/datasets --header '{self.api_authorization_header}'")
        assert not self.find_in_the_output(dashboard_charts, b'{"message":"Not found"}'), f'No dashboards found in the Superset\'s {DATABASE_NAME} database'
        assert not self.find_in_the_output(dashboard_datasets, b'{"message":"Not found"}'), f'No datasets found in the Superset\'s {DATABASE_NAME} database'
        assert self.decode_command_output(dashboard_charts).get("result")["charts"] != [], f'Loaded dashboards to the Superset\'s {DATABASE_NAME} have no charts'
        assert self.decode_command_output(dashboard_datasets).get("result") != [], f'Loaded datasets to the Superset\'s {DATABASE_NAME} are empty'

    @Utils.post_init_hook
    def status_swarm(self) -> None | AssertionError:
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'The Swarm node has not been activated'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: true'), f'The {SUPERSET_NODE} is supposed to be a Swarm manager, but it is not'
        # assert self.find_in_the_output(swarm_status_output, b'Nodes: 3'), 'The Swarm is expected to consist of three nodes in the pool, but the actual number varies.'

    def create_database_connection(self) -> int | AssertionError:
        payload: str = f'{{"engine":"mysql","configuration_method":"sqlalchemy_form","database_name":"MySQL","sqlalchemy_uri":"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{self.find_node_ip(MGMT_PRIMARY_NODE)}:6446/{DATABASE_NAME}"}}'
        mysql_connect: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --data '{payload}'")
        assert not self.find_in_the_output(mysql_connect, b'"message"'), f'Could not create database from API: {mysql_connect}'
        return self.decode_command_output(mysql_connect).get('id')

    def run_query(self, database_id: int) -> float | AssertionError:
        payload: str = f'{{"database_id":{database_id}, "runAsync": true, "sql": "SELECT * FROM {DATABASE_NAME}.logs;"}}'
        sqllab_run_query: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/sqllab/execute/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --data '{payload}'")
        assert not self.find_in_the_output(sqllab_run_query, b'"msg"'), f'SQL query execution failed with the following message: {sqllab_run_query}'
        assert not self.find_in_the_output(sqllab_run_query, b'"message"'), f'Could not execute query on: {DATABASE_NAME}'
        dttm_time_query_identifier: float = self.decode_command_output(sqllab_run_query).get("query").get("startDttm")
        return dttm_time_query_identifier
    
    def get_query_results(self, dttm_time_query_identifier: float):
        time.sleep(1)  # state refreshing
        query_result: dict = self.decode_command_output(
            self.run_command_on_the_container(f"curl --silent '{self.api_default_url}/query/updated_since?q=(last_updated_ms:{dttm_time_query_identifier})' --header 'Accept: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}'")
        )
        assert query_result.get("result")[0]['state'] == 'success', f'Could not find query state or returned unsuccessful: {query_result}'
        results_key: str = f"superset_results{query_result.get('result')[0]['resultsKey']}"
        assert self.redis.fetch_query_result(results_key), f'Query result with the {results_key} key can not be found in Redis'
        assert self.celery.find_processed_queries(), 'Query seems to be processed outside Celery worker'


class MgmtNodeFunctionalTests(BaseNodeConnection, metaclass=Utils):
    def __init__(self) -> None:
        super().__init__(node=MGMT_PRIMARY_NODE)

    @Utils.post_init_hook
    def status_cluster(self):
        cluster_status_output: bytes = self.run_command_on_the_container(f"docker exec {MGMT_HOSTNAME} mysqlsh --interactive --uri root:{MYSQL_PASSWORD}@{MGMT_PRIMARY_NODE}:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
        assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), 'The MySQL InnoDB cluster is not online or can not tolerate failures'
        assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), 'One primary instance is allowed for a given MySQL InnoDB cluster settings'

    @Utils.post_init_hook
    def status_routers(self):
        routers_status_output: bytes = self.run_command_on_the_container(f"docker exec {MGMT_HOSTNAME} mysqlsh --interactive --uri {MYSQL_USER}:{MYSQL_PASSWORD}@{MGMT_PRIMARY_NODE}:6446 --execute \"dba.getCluster(\'cluster\').listRouters();\"")

    @Utils.post_init_hook
    def status_swarm(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'The Swarm node has not been activated'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: false'), f'The {SUPERSET_NODE} is not supposed to be a Swarm manager, but it is'

    def check_mysql_after_disaster(self):
        self.stop_node(MYSQL_PRIMARY_NODE)
        time.sleep(_MYSQL_NODE_DISASTER_DELAY)
        new_mysql_primary_node: bytes = self.run_command_on_the_container(f"docker exec {MGMT_HOSTNAME} mysqlsh --interactive --uri {MYSQL_USER}:{MYSQL_PASSWORD}@{MGMT_PRIMARY_NODE}:6446 --sql --execute \"SELECT @@hostname;\"")
        assert self.find_in_the_output(new_mysql_primary_node, MYSQL_SECONDARY_NODES[0].encode('utf-8')), f'After stopping {MYSQL_PRIMARY_NODE}, {MYSQL_SECONDARY_NODES[0]} was expected to be selected as the new primary in a round-robin fashion. Selection process failed'

    def check_router_after_disaster(self):
        # self.stop_node(MGMT_PRIMARY_NODE)
        pass


if __name__ == '__main__':
    superset_functional = SupersetNodeFunctionalTests()
    database_id = superset_functional.create_database_connection()
    query_dttm = superset_functional.run_query(database_id)
    superset_functional.get_query_results(query_dttm)
    mgmt_functional = MgmtNodeFunctionalTests()
    mgmt_functional.check_mysql_after_disaster()
    mgmt_functional.check_router_after_disaster()