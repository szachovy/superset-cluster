"""
temporary
"""

import json
import time
import typing
import ssl
import socket

import container
import decorators


class Redis(container.ContainerConnection, metaclass=decorators.Overlay):
    def __init__(self, superset_container: str) -> None:
        super().__init__(container=superset_container)

    @decorators.Overlay.run_selected_methods_once
    def status(self) -> None | AssertionError:
        command: str = """python3 -c \
            'import redis; print(redis.StrictRedis(host=\"redis\", port=6379).ping())'
        """
        test_connection: bytes = self.run_command_on_the_container(command)
        assert \
            self.find_in_the_output(test_connection, b'True'), \
            f"The redis container is not responding\nCommand: {command}\nReturned: {test_connection}"

    def fetch_query_result(self, results_key: float) -> bool | AssertionError:
        command: str = f"""python3 -c
            'import redis; print(redis.StrictRedis(host=\"redis\", port=6379).get(\"{results_key}\"))'
        """
        query_result: bytes = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(query_result, b"None"), \
            f"Query results given key {results_key} not found in Redis\nCommand: {command}\nReturned: {query_result}"
        return True


class Celery(container.ContainerConnection, metaclass=decorators.Overlay):
    def __init__(self, superset_container: str) -> None:
        super().__init__(container=superset_container)
        self.superset_container: str = container
        self.celery_broker: str = "redis://redis:6379/0"
        self.celery_sql_lab_task_annotations: str = "sql_lab.get_sql_results"

    @decorators.Overlay.run_selected_methods_once
    def status(self) -> None | AssertionError:
        command: str = f"""python3 -c
            'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().ping())
        """
        test_connection: bytes = self.run_command_on_the_container(command)
        assert \
            self.find_in_the_output(test_connection, b"{'ok': 'pong'}"), \
            f"""The Celery process in the {self.superset_container} container on is not responding
                \nCommand: {command}\nReturned: {test_connection}
            """

    @decorators.Overlay.run_selected_methods_once
    def status_cache(self) -> None | AssertionError:
        command: str = f"""python3 -c
            'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().conf())
        """
        celery_workers_configuration: dict = self.decode_command_output(
            self.run_command_on_the_container(command)
        )
        celery_worker_id: str = next(iter(celery_workers_configuration))
        assert \
            all(
                features in celery_workers_configuration[celery_worker_id]["include"]
                for features in ['superset.tasks.cache', 'superset.tasks.scheduler']
            ), \
            f"""Celery cache and scheduler features in the {self.celery_broker} not found
                \nCommand: {command}\nReturned decoded: {celery_workers_configuration}
            """

    def find_processed_queries(self) -> bool | AssertionError:
        command = f"""python3 -c
            'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().stats())
        """
        celery_workers_stats: dict = self.decode_command_output(
            self.run_command_on_the_container(command)
        )
        celery_worker_id: str = next(iter(celery_workers_stats))
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
        self.redis: typing.Type = Redis(superset_container=superset_container)
        self.celery: typing.Type = Celery(superset_container=superset_container)
        self.virtual_ip_address: str = virtual_ip_address
        self.api_default_url: str = f"https://{virtual_ip_address}/api/v1"
        self.api_authorization_header: str = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header: str = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header: str = f"Cookie: session={self.login_to_superset()['session_token']}"

    def load_ssl_server_certificate(self) -> None:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with socket.create_connection((self.virtual_ip_address, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=self.virtual_ip_address) as ssl_sock:
                with open(
                    file="/opt/superset-testing/server_certificate.pem",
                    mode="wb",
                    encoding="utf-8"
                ) as certificate:
                    certificate.write(ssl.DER_cert_to_PEM_cert(ssl_sock.getpeercert(binary_form=True)).encode())
        self.copy_file_to_the_container(
            host_filepath="/opt/superset-testing/server_certificate.pem",
            container_dirpath="/app"
        )

    @decorators.Overlay.single_sign_on
    def login_to_superset_api(self) -> str | AssertionError:
        self.load_ssl_server_certificate()
        headers: str = "Content-Type: application/json"
        payload: str = "{{'username': 'superset', 'password': 'cluster', 'provider': 'db', 'refresh': true}}"
        command: str = f"""
            curl
                --cacert /app/server_certificate.pem
                --silent
                --url {self.api_default_url}/security/login
                --header '{headers}'
                --data '{payload}'
        """
        api_login_output: bytes = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(api_login_output, b'"message"'), \
            f"Could not log in to the Superset API {api_login_output}\nCommand: {command}\nReturned: {api_login_output}"
        return self.decode_command_output(api_login_output).get("access_token")

    @decorators.Overlay.single_sign_on
    def login_to_superset(self) -> dict[str, str] | AssertionError:
        command: str = f"""
            curl
            --cacert /app/server_certificate.pem
            --include
            --url {self.api_default_url}/security/csrf_token/
            --header '{self.api_authorization_header}'
        """
        csrf_login_request: bytes = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(csrf_login_request, b'"msg"'), \
            f"Could not pass login request {csrf_login_request}\nCommand: {command}\nReturned: {csrf_login_request}"
        session_request_cookie: str = self.extract_session_cookie(csrf_login_request)
        csrf_token: str = json.loads(csrf_login_request.decode('utf-8').split('\r\n\r\n')[1]).get("result")
        command: str = f"""
            curl
                --location
                --cacert /app/server_certificate.pem
                --include
                --url https://{self.virtual_ip_address}/login/
                --header 'Cookie: session={session_request_cookie}'
                --data 'csrf_token={csrf_token}'
        """
        superset_login_request: bytes = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(superset_login_request, b"Redirecting..."), \
            f"""Invalid login request to Superset. Could not get a response from the server.
                Check if it is possible to log in to the server manually
                \nCommand: {command}\nReturned: {superset_login_request}"""
        superset_login_session_cookie: str = self.extract_session_cookie(superset_login_request)
        return {
            "csrf_token": csrf_token,
            "session_token": superset_login_session_cookie
        }

    @decorators.Overlay.run_selected_methods_once
    def status_database(self) -> None | AssertionError:
        with open(
            file="/opt/superset-cluster/mysql-mgmt/mysql_superset_password",
            mode="r",
            encoding="utf-8"
        ) as mysql_superset_password:
            payload: str = f"""
                {
                    {
                        "database_name": "MySQL",
                        "sqlalchemy_uri": f"mysql+mysqlconnector://superset:{mysql_superset_password.read().strip()}@{self.virtual_ip_address}:6446/superset",
                        "impersonate_user": "false"
                    }
                }
            """    # noqa: E501
            command: str = f"""
                curl
                    --location
                    --cacert /app/server_certificate.pem
                    --silent
                    {self.api_default_url}/database/test_connection/
                    --header 'Content-Type: application/json'
                    --header '{self.api_authorization_header}'
                    --header '{self.api_csrf_header}'
                    --header '{self.api_session_header}'
                    --header 'Referer: https://{self.virtual_ip_address}'
                    --data '{payload}'
            """
            test_database_connection: bytes = self.run_command_on_the_container(command)
            assert \
                self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), \
                f"""Could not connect to the superset database on {self.virtual_ip_address} port 6446, \
                    the database is either down or not configured according to the given SQL Alchemy URI \
                    \nCommand: {command}\nReturned: {test_database_connection} \
                """

    @decorators.Overlay.run_selected_methods_once
    def status_swarm(self) -> None | AssertionError:
        swarm_info = self.info()["Swarm"]
        assert \
            swarm_info["LocalNodeState"] == "active", \
            "The Swarm node has not been activated"
        assert \
            swarm_info["ControlAvailable"] is True, \
            "The testing localhost is supposed to be a Swarm manager, but it is not"

    def run_query(self) -> float | AssertionError:
        payload: str = "{{'database_id': 1, 'runAsync': true, 'sql': 'SELECT * FROM superset.logs;'}}"
        command: str = f"""
            curl
                --location
                --cacert /app/server_certificate.pem
                --silent
                {self.api_default_url}/sqllab/execute/
                --header 'Content-Type: application/json'
                --header '{self.api_authorization_header}'
                --header '{self.api_session_header}'
                --header '{self.api_csrf_header}'
                --header 'Referer: https://{self.virtual_ip_address}'
                --data '{payload}'
        """
        sqllab_run_query: bytes = self.run_command_on_the_container(command)
        assert \
            not self.find_in_the_output(sqllab_run_query, b'"msg"'), \
            f"SQL query execution failed\nCommand: {command}\nReturned: {sqllab_run_query}"
        assert \
            not self.find_in_the_output(sqllab_run_query, b'"message"'), \
            f"Could not execute SQL query\nCommand: {command}\nReturned: {sqllab_run_query}"
        dttm_time_query_identifier: float = self.decode_command_output(sqllab_run_query).get("query").get("startDttm")
        return dttm_time_query_identifier

    def get_query_results(self, dttm_time_query_identifier: float) -> None | AssertionError:
        time.sleep(45)  # state refreshing
        command: str = f"""
            curl
                --location
                --cacert /app/server_certificate.pem
                --silent
                '{self.api_default_url}/query/updated_since?q=(last_updated_ms:{dttm_time_query_identifier})'
                --header 'Accept: application/json'
                --header '{self.api_authorization_header}'
                --header '{self.api_session_header}'
                --header 'Referer: https://{self.virtual_ip_address}'
                --header '{self.api_csrf_header}'
        """
        query_result: dict = self.decode_command_output(
            self.run_command_on_the_container(command)
        )
        assert \
            query_result.get("result")[0]["state"] == "success", \
            f"Could not find query state or returned unsuccessful\nCommand: {command}\nReturned decoded: {query_result}"
        results_key: str = f"superset_results{query_result.get('result')[0]['resultsKey']}"
        assert \
            self.redis.fetch_query_result(results_key), \
            f"Query result with the {results_key} key can not be found in Redis after\nCommand: {command}"
        assert \
            self.celery.find_processed_queries(), \
            f"Query seems to be processed outside Celery worker after\nCommand: {command}"
