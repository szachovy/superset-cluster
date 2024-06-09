
import argparse
import ast
import functools
import json
import re
import threading
import time
import typing

import docker
import requests

import data_structures

class ArgumentParser:
    def __init__(self) -> None:
        self.parser: argparse.ArgumentParser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        self.parser.add_argument('--nodes', type=int)
        self.parser.add_argument('--node-prefix', type=str)
        self.parser.add_argument('--mgmt-hostname', type=str)
        self.parser.add_argument('--mysql-user', type=str)
        self.parser.add_argument('--mysql-password', type=str)
        self.parser.add_argument('--redis-hostname', type=str)
        self.parser.add_argument('--redis-port', type=int)
        self.parser.add_argument('--celery-sql-lab-task-annotations', type=str)
        self.parser.add_argument('--celery-broker', type=str)
        self.parser.add_argument('--superset-hostname', type=str)
        self.parser.add_argument('--database-name', type=str)
        self.parser.add_argument('--superset-password', type=str)

    def parse_arguments(self) -> argparse.Namespace:
        return self.parser.parse_args()


class Redis(data_structures.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self) -> None:
        super().__init__(node=self.arguments.superset_hostname)

    @data_structures.Overlay.post_init_hook
    def status(self) -> None | AssertionError:
        test_connection: bytes = self.run_command_on_the_container(f"python3 -c 'import redis; print(redis.StrictRedis(host=\"{self.arguments.redis_hostname}\", port={self.arguments.redis_port}).ping())'")
        assert self.find_in_the_output(test_connection, b'True'), f'The Redis container {self.arguments.redis_hostname} on {self.arguments.node_prefix}-4 node is not responding or not working properly'

    def fetch_query_result(self, results_key: float) -> bool | AssertionError:
        query_result: bytes = self.run_command_on_the_container(f"python3 -c 'import redis; print(redis.StrictRedis(host=\"{self.arguments.redis_hostname}\", port={self.arguments.redis_port}).get(\"{results_key}\"))'")
        assert not self.find_in_the_output(query_result, b"None"), f'Query results given key {results_key} not found in Redis'
        return True


class Celery(data_structures.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self) -> None:
        super().__init__(node=self.arguments.superset_hostname) 

    @data_structures.ContainerUtilities.post_init_hook
    def status(self) -> None | AssertionError: 
        test_connection: bytes = self.run_command_on_the_container(f"python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.arguments.celery_broker}\").control.inspect().ping())'")
        assert self.find_in_the_output(test_connection, b"{'ok': 'pong'}"), f'The Celery process in the {self.arguments.superset_hostname} container on {self.arguments.node_prefix}-4 node is not responding or not working properly'

    @data_structures.ContainerUtilities.post_init_hook
    def status_cache(self) -> None | AssertionError:
        celery_workers_configuration: dict = self.decode_command_output(
            self.run_command_on_the_container(f"python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.arguments.celery_broker}\").control.inspect().conf())'")
        )
        celery_worker_id: str = next(iter(celery_workers_configuration))
        assert all(features in celery_workers_configuration[celery_worker_id]['include'] for features in ['superset.tasks.cache', 'superset.tasks.scheduler']), f'Celery cache and scheduler features in the {self.arguments.celery_broker} not found'

    def find_processed_queries(self) -> bool | AssertionError:
        celery_workers_stats: dict = self.decode_command_output(
            self.run_command_on_the_container(f"python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.arguments.celery_broker}\").control.inspect().stats())'")
        )
        celery_worker_id: str = next(iter(celery_workers_stats))
        assert celery_workers_stats[celery_worker_id]['total'][self.arguments.celery_sql_lab_task_annotations] > 0, f'Executed SQL Lab queries are not processed or registered by Celery on {self.arguments.node_prefix}-4, check the Celery worker process on the {self.arguments.superset_hostname}'
        return True


class SupersetNodeFunctionalTests(data_structures.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self) -> None:
        super().__init__(node=self.arguments.superset_hostname) 
        self.api_default_url: str = "http://localhost:8088/api/v1"
        self.api_authorization_header: str = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header: str = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header: str = f"Cookie: session={self.login_to_superset()['session_token']}"
        self.celery: typing.Type = Celery()
        self.redis: typing.Type = Redis()

    @data_structures.Overlay.singleton_function
    def login_to_superset_api(self) -> str | AssertionError:
        headers: str = "Content-Type: application/json"
        payload: str = f'{{"username": "admin", "password": "{self.arguments.superset_password}", "provider": "db", "refresh": true}}'
        api_login_output: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/security/login --header '{headers}' --data '{payload}'")
        assert not self.find_in_the_output(api_login_output, b'"message"'), f'Could not log in to the Superset API {api_login_output}'
        return self.decode_command_output(api_login_output).get("access_token")

    @data_structures.Overlay.singleton_function
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
        payload: str = f'{{"database_name": "MySQL", "sqlalchemy_uri": "mysql+mysqlconnector://{self.arguments.mysql_user}:{self.arguments.mysql_password}@{self.find_node_ip(self.mgmt_primary_node)}:6446/{self.arguments.database_name}", "impersonate_user": false}}'
        test_database_connection: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/test_connection/ --header '{self.api_authorization_header}' --header '{self.api_csrf_header}' --header '{self.api_session_header}' --header 'Content-Type: application/json' --data '{payload}'")
        assert self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), f'Could not connect to the {self.arguments.database_name} on {self.mgmt_primary_node} port 6446, the database is either down or not configured according to the given SQL Alchemy URI'

    @data_structures.Overlay.post_init_hook
    def status_datasets(self) -> None | AssertionError:
        dashboard_charts: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1 --header '{self.api_authorization_header}'")
        dashboard_datasets: bytes = self.run_command_on_the_container(f"curl --silent --url {self.api_default_url}/dashboard/1/datasets --header '{self.api_authorization_header}'")
        assert not self.find_in_the_output(dashboard_charts, b'{"message":"Not found"}'), f'No dashboards found in the Superset\'s {self.arguments.database_name} database'
        assert not self.find_in_the_output(dashboard_datasets, b'{"message":"Not found"}'), f'No datasets found in the Superset\'s {self.arguments.database_name} database'
        assert self.decode_command_output(dashboard_charts).get("result")["charts"] != [], f'Loaded dashboards to the Superset\'s {self.arguments.database_name} have no charts'
        assert self.decode_command_output(dashboard_datasets).get("result") != [], f'Loaded datasets to the Superset\'s {self.arguments.database_name} are empty'

    @data_structures.Overlay.post_init_hook
    def status_swarm(self) -> None | AssertionError:
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'The Swarm node has not been activated'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: true'), f'The {self.superset_node: str }  is supposed to be a Swarm manager, but it is not'
        # assert self.find_in_the_output(swarm_status_output, b'Nodes: 3'), 'The Swarm is expected to consist of three nodes in the pool, but the actual number varies.'

    def create_database_connection(self) -> int | AssertionError:
        payload: str = f'{{"engine":"mysql","configuration_method":"sqlalchemy_form","database_name":"MySQL","sqlalchemy_uri":"mysql+mysqlconnector://{self.arguments.mysql_user}:{self.arguments.mysql_password}@{self.find_node_ip(self.mgmt_primary_node)}:6446/{self.arguments.database_name}"}}'
        mysql_connect: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/database/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --data '{payload}'")
        assert not self.find_in_the_output(mysql_connect, b'"message"'), f'Could not create database from API: {mysql_connect}'
        return self.decode_command_output(mysql_connect).get('id')

    def run_query(self, database_id: int) -> float | AssertionError:
        payload: str = f'{{"database_id":{database_id}, "runAsync": true, "sql": "SELECT * FROM {self.arguments.database_name}.logs;"}}'
        sqllab_run_query: bytes = self.run_command_on_the_container(f"curl --silent {self.api_default_url}/sqllab/execute/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --data '{payload}'")
        assert not self.find_in_the_output(sqllab_run_query, b'"msg"'), f'SQL query execution failed with the following message: {sqllab_run_query}'
        assert not self.find_in_the_output(sqllab_run_query, b'"message"'), f'Could not execute query on: {self.arguments.database_name}'
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


if __name__ == '__main__':
    superset_functional = SupersetNodeFunctionalTests()
    database_id = superset_functional.create_database_connection()
    query_dttm = superset_functional.run_query(database_id)
    superset_functional.get_query_results(query_dttm)
