"""
Superset Node Functional Tests

This module provides classes and methods for testing the
Superset node ecosystem, including Redis, Celery, and Superset itself,
within containerized environments.

Classes:
--------
- Redis:
  A class to manage and test Redis service operations within a specified
  container. It verifies connectivity and fetches query results.

- Celery:
  A class to manage and validate the Celery service associated with the
  Superset container. It verifies connectivity and performs tests related
  to cache and query processing.

- Superset:
  A class to manage and interact with Superset services within a container.
  It handles login operations, checks the status of the database and Swarm
  configuration, runs SQL queries, and retrieves query results.

Key Functionalities:
--------------------
- Service Status Checks: Each class includes methods that verify the
  operational status of core services (e.g., Redis ping, Celery worker status,
  and Superset database connection) to ensure the environment is functioning
  properly.

- Authenticated API Access: The `Superset` class supports secure API
  interactions by managing SSL certificates and handling session-based login
  for accessing and testing Superset features.

- Query Execution and Result Retrieval: Through the Superset class, users
  can execute SQL queries, track their execution status, and retrieve results,
  while leveraging Redis and Celery to monitor processing and caching
  capabilities.

- Configuration Validation: The module performs checks on critical
  configurations such as database connectivity, Swarm node activation, and
  the presence of necessary Celery worker features, to confirm that services
  are properly configured for use within the Superset ecosystem.


Example Usage:
--------------
To use the `Superset` class, create an instance with the container name and
virtual IP address, after necessary checks it runs query pipeline involving
all the connectivity components, results are parsed with the expectations.
Status methods are called automatically.

```python
superset_functional = Superset(
    superset_container="superset.1.qwecnevnouwoebvuwec",
    virtual_ip_address="192.168.1.100"
)
query_dttm = superset_functional.run_query()
superset_functional.get_query_results(query_dttm)
"""

import json
import time
import ssl
import socket

import container
import decorators


class Redis(container.ContainerConnection, metaclass=decorators.Overlay):
    def __init__(self, superset_container: str) -> None:
        super().__init__(container=superset_container)

    @decorators.Overlay.run_selected_methods_once
    def status(self) -> None:
        command = """python3 -c \
            'import redis; print(redis.StrictRedis(host=\"redis\", port=6379).ping())'
        """
        test_connection = self.run_command_on_the_container(command)
        assert \
            self.find_in_the_output(test_connection, b'True'), \
            f"The redis container is not responding\nCommand: {command!r}\nReturned: {test_connection!r}"

    def fetch_query_result(self, results_key: str) -> bool:
        command = f"""python3 -c
            'import redis; print(redis.StrictRedis(host=\"redis\", port=6379).get(\"{results_key}\"))'
        """
        query_result = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(query_result, b"None"), \
            f"""Query results given key {results_key} not found in Redis
                \nCommand: {command!r}\nReturned: {query_result!r}
            """
        return True


class Celery(container.ContainerConnection, metaclass=decorators.Overlay):
    def __init__(self, superset_container: str) -> None:
        super().__init__(container=superset_container)
        self.superset_container = container
        self.celery_broker = "redis://redis:6379/0"
        self.celery_sql_lab_task_annotations = "sql_lab.get_sql_results"

    @decorators.Overlay.run_selected_methods_once
    def status(self) -> None:
        command = f"""python3 -c
            'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().ping())'
        """
        test_connection = self.run_command_on_the_container(command)
        assert \
            self.find_in_the_output(test_connection, b"{'ok': 'pong'}"), \
            f"""The Celery process in the {self.superset_container} container on is not responding
                \nCommand: {command!r}\nReturned: {test_connection!r}
            """

    @decorators.Overlay.run_selected_methods_once
    def status_cache(self) -> None:
        command = f"""python3 -c
            'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().conf())'
        """
        celery_workers_configuration: dict = self.decode_command_output(
            self.run_command_on_the_container(command)
        )
        celery_worker_id = next(iter(celery_workers_configuration))
        assert \
            all(
                features in celery_workers_configuration[celery_worker_id]["include"]
                for features in ['superset.tasks.cache', 'superset.tasks.scheduler']
            ), \
            f"""Celery cache and scheduler features in the {self.celery_broker} not found
                \nCommand: {command}\nReturned decoded: {celery_workers_configuration}
            """

    def find_processed_queries(self) -> bool:
        command = f"""python3 -c
            'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().stats())'
        """
        celery_workers_stats: dict = self.decode_command_output(
            self.run_command_on_the_container(command)
        )
        celery_worker_id = next(iter(celery_workers_stats))
        assert \
            celery_workers_stats[celery_worker_id]["total"][self.celery_sql_lab_task_annotations] > 0, \
            f"""Executed SQL Lab queries are not processed or registered by Celery,
                check the Celery worker process on the {self.superset_container}
                \nCommand: {command}\nReturned decoded: {celery_workers_stats}
            """
        return True


class Superset(container.ContainerConnection, metaclass=decorators.Overlay):
    def __init__(self, superset_container: str, virtual_ip_address: str) -> None:
        super().__init__(container=superset_container)
        self.redis = Redis(superset_container=superset_container)
        self.celery = Celery(superset_container=superset_container)
        self.virtual_ip_address = virtual_ip_address
        self.api_default_url = f"https://{virtual_ip_address}/api/v1"
        self.api_authorization_header = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header = f"Cookie: session={self.login_to_superset()['session_token']}"

    def load_ssl_server_certificate(self) -> None:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with socket.create_connection((self.virtual_ip_address, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=self.virtual_ip_address) as ssl_sock:
                certificate_binary = ssl_sock.getpeercert(binary_form=True)
                if certificate_binary is not None:
                    with open(
                        file="/opt/superset-testing/server_certificate.pem",
                        mode="wb"
                    ) as certificate:
                        certificate.write(ssl.DER_cert_to_PEM_cert(certificate_binary).encode())
        self.copy_file_to_the_container(
            host_filepath="/opt/superset-testing/server_certificate.pem",
            container_dirpath="/app"
        )

    @decorators.Overlay.single_sign_on
    def login_to_superset_api(self) -> str:
        self.load_ssl_server_certificate()
        headers = "Content-Type: application/json"
        payload = '{"username": "superset", "password": "cluster", "provider": "db", "refresh": true}'
        command = f"""
            curl \
                --cacert /app/server_certificate.pem \
                --silent \
                --url {self.api_default_url}/security/login \
                --header '{headers}' \
                --data '{payload}'
        """
        api_login_output = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(api_login_output, b'"message"'), \
            f"""Could not log in to the Superset API {api_login_output!r}
                \nCommand: {command!r}\nReturned: {api_login_output!r}
            """
        return str(self.decode_command_output(api_login_output).get("access_token"))

    @decorators.Overlay.single_sign_on
    def login_to_superset(self) -> dict:
        command = f"""
            curl \
            --cacert /app/server_certificate.pem \
            --include \
            --url {self.api_default_url}/security/csrf_token/ \
            --header '{self.api_authorization_header}'
        """
        csrf_login_request = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(csrf_login_request, b'"msg"'), \
            f"""Could not pass login request {csrf_login_request!r}
                \nCommand: {command!r}\nReturned: {csrf_login_request!r}
            """
        session_request_cookie = self.extract_session_cookie(csrf_login_request)
        csrf_token = json.loads(csrf_login_request.decode('utf-8').split('\r\n\r\n')[1]).get("result")
        command = f"""
            curl \
                --location \
                --cacert /app/server_certificate.pem \
                --include \
                --url https://{self.virtual_ip_address}/login/ \
                --header 'Cookie: session={session_request_cookie}' \
                --data 'csrf_token={csrf_token}'
        """    # type: ignore[no-redef]
        superset_login_request = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(superset_login_request, b"Redirecting..."), \
            f"""Invalid login request to Superset. Could not get a response from the server.
                Check if it is possible to log in to the server manually
                \nCommand: {command!r}\nReturned: {superset_login_request!r}"""
        superset_login_session_cookie = self.extract_session_cookie(superset_login_request)
        return {
            "csrf_token": csrf_token,
            "session_token": superset_login_session_cookie
        }

    @decorators.Overlay.run_selected_methods_once
    def status_database(self) -> None:
        with open(
            file="/opt/superset-cluster/mysql-mgmt/mysql_superset_password",
            mode="r",
            encoding="utf-8"
        ) as mysql_superset_password:
            payload = f'''
            {{
                "database_name": "MySQL",
                "sqlalchemy_uri": "mysql+mysqlconnector://superset:{mysql_superset_password.read().strip()}@{self.virtual_ip_address}:6446/superset",
                "impersonate_user": "false"
            }}
            '''    # noqa: E501
            command = f"""
                curl \
                    --location \
                    --cacert /app/server_certificate.pem \
                    --silent \
                    {self.api_default_url}/database/test_connection/ \
                    --header 'Content-Type: application/json' \
                    --header '{self.api_authorization_header}' \
                    --header '{self.api_csrf_header}' \
                    --header '{self.api_session_header}' \
                    --header 'Referer: https://{self.virtual_ip_address}' \
                    --data '{payload}'
            """
            test_database_connection = self.run_command_on_the_container(command)
            assert \
                self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), \
                f"""Could not connect to the superset database on {self.virtual_ip_address} port 6446, \
                    the database is either down or not configured according to the given SQL Alchemy URI \
                    \nCommand: {command!r}\nReturned: {test_database_connection!r} \
                """

    @decorators.Overlay.run_selected_methods_once
    def status_swarm(self) -> None:
        swarm_info = self.info()["Swarm"]
        assert \
            swarm_info["LocalNodeState"] == "active", \
            "The Swarm node has not been activated"
        assert \
            swarm_info["ControlAvailable"] is True, \
            "The testing localhost is supposed to be a Swarm manager, but it is not"

    def run_query(self) -> float:
        payload = '{{"database_id": 1, "runAsync": true, "sql": "SELECT * FROM superset.logs;"}}'
        command = f"""
            curl \
                --location \
                --cacert /app/server_certificate.pem \
                --silent \
                {self.api_default_url}/sqllab/execute/ \
                --header 'Content-Type: application/json' \
                --header '{self.api_authorization_header}' \
                --header '{self.api_session_header}' \
                --header '{self.api_csrf_header}' \
                --header 'Referer: https://{self.virtual_ip_address}' \
                --data '{payload}'
        """
        sqllab_run_query = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(sqllab_run_query, b'"msg"'), \
            f"SQL query execution failed\nCommand: {command!r}\nReturned: {sqllab_run_query!r}"
        assert \
            not self.find_in_the_output(sqllab_run_query, b'"message"'), \
            f"Could not execute SQL query\nCommand: {command!r}\nReturned: {sqllab_run_query!r}"
        sqllab_query_details: dict | None = self.decode_command_output(sqllab_run_query).get("query")
        if isinstance(sqllab_query_details, dict):
            dttm_time_query_identifier = sqllab_query_details.get("startDttm")
            if isinstance(dttm_time_query_identifier, float):
                return dttm_time_query_identifier
            raise ValueError(f"Could not get startDttm timestamp from {sqllab_run_query!r}")
        raise ValueError(f"Could not find query details in {sqllab_run_query!r}")

    def get_query_results(self, dttm_time_query_identifier: float) -> None:
        time.sleep(45)  # state refreshing
        command = f"""
            curl \
                --location \
                --cacert /app/server_certificate.pem \
                --silent \
                '{self.api_default_url}/query/updated_since?q=(last_updated_ms:{dttm_time_query_identifier})' \
                --header 'Accept: application/json' \
                --header '{self.api_authorization_header}' \
                --header '{self.api_session_header}' \
                --header 'Referer: https://{self.virtual_ip_address}' \
                --header '{self.api_csrf_header}'
        """
        query_result = self.decode_command_output(
            self.run_command_on_the_container(command)
        )
        list_of_results = query_result.get("result")
        if isinstance(list_of_results, list):
            first_result = list_of_results[0]
            if isinstance(first_result, dict):
                assert \
                    first_result["state"] == "success", \
                    f"""Could not find query state or returned unsuccessful
                        \nCommand: {command}\nReturned decoded: {query_result}
                    """
                results_key = f"superset_results{first_result['resultsKey']}"
                assert \
                    self.redis.fetch_query_result(results_key), \
                    f"Query result with the {results_key} key can not be found in Redis after\nCommand: {command}"
                assert \
                    self.celery.find_processed_queries(), \
                    f"Query seems to be processed outside Celery worker after\nCommand: {command}"
            else:
                raise ValueError(f"Could not fetch first result from {query_result} or the result is empty")
        else:
            raise ValueError(f"Could not get list of results from {query_result}")
