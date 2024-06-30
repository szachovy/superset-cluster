
import json
import time
import typing

import container_connection
import data_structures


class Redis(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, superset_hostname: str, redis_hostname: str, redis_port: int, node_prefix: str) -> None:
        super().__init__(node=superset_hostname)
        self.redis_hostname: str = redis_hostname
        self.redis_port: int = redis_port
        self.superset_node: str = f"{node_prefix}-4"

    @data_structures.Overlay.post_init_hook
    def status(self) -> None | AssertionError:
        test_connection: bytes = self.run_command_on_the_container(f"python3 -c 'import redis; print(redis.StrictRedis(host=\"{self.redis_hostname}\", port={self.redis_port}).ping())'")
        assert self.find_in_the_output(test_connection, b'True'), f'The Redis container {self.redis_hostname} on {self.superset_node} node is not responding or not working properly'

    def fetch_query_result(self, results_key: float) -> bool | AssertionError:
        query_result: bytes = self.run_command_on_the_container(f"python3 -c 'import redis; print(redis.StrictRedis(host=\"{self.redis_hostname}\", port={self.redis_port}).get(\"{results_key}\"))'")
        assert not self.find_in_the_output(query_result, b"None"), f'Query results given key {results_key} not found in Redis'
        return True


class Celery(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, superset_hostname: str, celery_broker: str, celery_sql_lab_task_annotations: str, node_prefix: str) -> None:
        super().__init__(node=superset_hostname)
        self.superset_hostname: str = superset_hostname
        self.celery_broker: str = celery_broker
        self.celery_sql_lab_task_annotations: str = celery_sql_lab_task_annotations
        self.superset_node: str = f"{node_prefix}-4"

    @data_structures.Overlay.post_init_hook
    def status(self) -> None | AssertionError:
        command: str = f"python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().ping())'"
        test_connection: bytes = self.run_command_on_the_container(command)
        assert self.find_in_the_output(test_connection, b"{'ok': 'pong'}"), f'The Celery process in the {self.superset_hostname} container on {self.superset_node} node is not responding or not working properly, output after {command} is {test_connection}'

    @data_structures.Overlay.post_init_hook
    def status_cache(self) -> None | AssertionError:
        celery_workers_configuration: dict = self.decode_command_output(
            self.run_command_on_the_container(f"python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().conf())'")
        )
        celery_worker_id: str = next(iter(celery_workers_configuration))
        assert all(features in celery_workers_configuration[celery_worker_id]['include'] for features in ['superset.tasks.cache', 'superset.tasks.scheduler']), f'Celery cache and scheduler features in the {self.celery_broker} not found'

    def find_processed_queries(self) -> bool | AssertionError:
        celery_workers_stats: dict = self.decode_command_output(
            self.run_command_on_the_container(f"python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().stats())'")
        )
        celery_worker_id: str = next(iter(celery_workers_stats))
        assert celery_workers_stats[celery_worker_id]['total'][self.celery_sql_lab_task_annotations] > 0, f'Executed SQL Lab queries are not processed or registered by Celery on {self.superset_node}, check the Celery worker process on the {self.superset_hostname}'
        return True


class SupersetNodeFunctionalTests(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, node_prefix: str, mysql_user: str, mysql_password: str, redis_hostname: str, redis_port: int, celery_sql_lab_task_annotations: str, celery_broker: str, superset_hostname: str, database_name: str, superset_password: str) -> None:
        super().__init__(node=superset_hostname)
        self.celery: typing.Type = Celery(superset_hostname, celery_broker, celery_sql_lab_task_annotations, node_prefix)
        self.redis: typing.Type = Redis(superset_hostname, redis_hostname, redis_port, node_prefix)
        self.mysql_user: str = mysql_user
        self.mysql_password: str = mysql_password
        self.superset_hostname: str = superset_hostname
        self.database_name: str = database_name
        self.superset_password: str = superset_password
        self.mgmt_primary_node: str = f"{node_prefix}-0"
        self.superset_node: str = f"{node_prefix}-4"
        self.api_default_url: str = "http://localhost:8088/api/v1"
        self.api_authorization_header: str = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header: str = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header: str = f"Cookie: session={self.login_to_superset()['session_token']}"

    @data_structures.Overlay.single_sign_on
    def login_to_superset_api(self) -> str | AssertionError:
        headers: str = "Content-Type: application/json"
        payload: str = f'{{"username": "admin", "password": "{self.superset_password}", "provider": "db", "refresh": true}}'
        api_login_output: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/security/login --header '{headers}' --data '{payload}'")
        assert not self.find_in_the_output(api_login_output, b'"message"'), f'Could not log in to the Superset API {api_login_output}'
        return self.decode_command_output(api_login_output).get("access_token")

    @data_structures.Overlay.single_sign_on
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

    @data_structures.Overlay.post_init_hook
    def status_database(self) -> None | AssertionError:
        payload: str = f'{{"database_name": "MySQL", "sqlalchemy_uri": "mysql+mysqlconnector://{self.mysql_user}:{self.mysql_password}@{self.find_node_ip(self.mgmt_primary_node)}:6446/{self.database_name}", "impersonate_user": false}}'
        test_database_connection: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/test_connection/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_csrf_header}' --header '{self.api_session_header}' --data '{payload}'")
        assert self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), f'Could not connect to the {self.database_name} on {self.mgmt_primary_node} port 6446, the database is either down or not configured according to the given SQL Alchemy URI'

    @data_structures.Overlay.post_init_hook
    def status_datasets(self) -> None | AssertionError:
        dashboard_charts: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1 --header '{self.api_authorization_header}'")
        dashboard_datasets: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1/datasets --header '{self.api_authorization_header}'")
        assert not self.find_in_the_output(dashboard_charts, b'{"message":"Not found"}'), f'No dashboards found in the Superset'
        assert not self.find_in_the_output(dashboard_datasets, b'{"message":"Not found"}'), f'No datasets found in the Superset'
        assert self.decode_command_output(dashboard_charts).get("result")["charts"] != [], f'Pre-loaded dashboards in the Superset have no charts'
        assert self.decode_command_output(dashboard_datasets).get("result") != [], f'Pre-loaded datasets in the Superset are empty'

    @data_structures.Overlay.post_init_hook
    def status_swarm(self) -> None | AssertionError:
        swarm_info = self.info()['Swarm']
        assert swarm_info['LocalNodeState'] == 'active', 'The Swarm node has not been activated'
        assert swarm_info['ControlAvailable'] is True, f'The {self.superset_node} is supposed to be a Swarm manager, but it is not'
        # assert swarm_info['Nodes'] == 3, f'The Swarm is expected to consist of 3 nodes instead of {swarm_info["Nodes"]} in the pool.'

    def create_database_connection(self) -> int | AssertionError:
        payload: str = f'{{"engine": "mysql", "configuration_method": "sqlalchemy_form", "database_name": "MySQL", "sqlalchemy_uri": "mysql+mysqlconnector://{self.mysql_user}:{self.mysql_password}@{self.find_node_ip(self.mgmt_primary_node)}:6446/{self.database_name}"}}'
        mysql_connect: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --data '{payload}'")
        assert not self.find_in_the_output(mysql_connect, b'"message"'), f'Could not create database from API: {mysql_connect}'
        return self.decode_command_output(mysql_connect).get('id')

    def run_query(self, database_id: int) -> float | AssertionError:
        payload: str = f'{{"database_id": {database_id}, "runAsync": true, "sql": "SELECT * FROM {self.database_name}.logs;"}}'
        sqllab_run_query: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/sqllab/execute/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --data '{payload}'")
        assert not self.find_in_the_output(sqllab_run_query, b'"msg"'), f'SQL query execution failed with the following message: {sqllab_run_query}'
        assert not self.find_in_the_output(sqllab_run_query, b'"message"'), f'Could not execute query on: {self.database_name}'
        dttm_time_query_identifier: float = self.decode_command_output(sqllab_run_query).get("query").get("startDttm")
        return dttm_time_query_identifier
    
    def get_query_results(self, dttm_time_query_identifier: float):
        time.sleep(5)  # state refreshing
        query_result: dict = self.decode_command_output(
            self.run_command_on_the_container(f"curl --silent '{self.api_default_url}/query/updated_since?q=(last_updated_ms:{dttm_time_query_identifier})' --header 'Accept: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}'")
        )
        assert query_result.get("result")[0]['state'] == 'success', f'Could not find query state or returned unsuccessful: {query_result}'
        results_key: str = f"superset_results{query_result.get('result')[0]['resultsKey']}"
        assert self.redis.fetch_query_result(results_key), f'Query result with the {results_key} key can not be found in Redis'
        assert self.celery.find_processed_queries(), 'Query seems to be processed outside Celery worker'
