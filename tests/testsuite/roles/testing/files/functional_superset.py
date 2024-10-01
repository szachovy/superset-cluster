
import json
import time
import typing
import ssl
import socket

import container_connection
import data_structures


class Redis(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, container: str) -> None:
        super().__init__(container=container)

    @data_structures.Overlay.post_init_hook
    def status(self) -> None | AssertionError:
        test_connection: bytes = self.run_command_on_the_container(f"python3 -c 'import redis; print(redis.StrictRedis(host=\"redis\", port=6379).ping())'")
        assert self.find_in_the_output(test_connection, b'True'), f'The redis container is not responding'

    def fetch_query_result(self, results_key: float) -> bool | AssertionError:
        query_result: bytes = self.run_command_on_the_container(f"python3 -c 'import redis; print(redis.StrictRedis(host=\"redis\", port=6379).get(\"{results_key}\"))'")
        assert not self.find_in_the_output(query_result, b"None"), f'Query results given key {results_key} not found in Redis'
        return True


class Celery(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, container: str) -> None:
        super().__init__(container=container)
        self.superset_container: str = container
        self.celery_broker: str = f"redis://redis:6379/0"
        self.celery_sql_lab_task_annotations: str = "sql_lab.get_sql_results"

    @data_structures.Overlay.post_init_hook
    def status(self) -> None | AssertionError:
        command: str = f"python3 -c 'import celery; print(celery.Celery(\"tasks\", broker=\"{self.celery_broker}\").control.inspect().ping())'"
        test_connection: bytes = self.run_command_on_the_container(command)
        assert self.find_in_the_output(test_connection, b"{'ok': 'pong'}"), f'The Celery process in the {self.superset_container} container on is not responding, output after {command} is {test_connection}'

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
        assert celery_workers_stats[celery_worker_id]['total'][self.celery_sql_lab_task_annotations] > 0, f'Executed SQL Lab queries are not processed or registered by Celery, check the Celery worker process on the {self.superset_container}'
        return True


class Superset(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, superset_container: str, virtual_ip_address: str) -> None:
        super().__init__(container=superset_container)
        self.redis: typing.Type = Redis(container=superset_container)
        self.celery: typing.Type = Celery(container=superset_container)
        self.virtual_ip_address: str = virtual_ip_address
        self.api_default_url: str = f"https://{virtual_ip_address}/api/v1"
        self.api_authorization_header: str = f"Authorization: Bearer {self.login_to_superset_api()}"
        self.api_csrf_header: str = f"X-CSRFToken: {self.login_to_superset()['csrf_token']}"
        self.api_session_header: str = f"Cookie: session={self.login_to_superset()['session_token']}"

    @data_structures.Overlay.single_sign_on
    def login_to_superset_api(self) -> str | AssertionError:
        headers: str = "Content-Type: application/json"
        payload: str = f'{{"username": "superset", "password": "cluster", "provider": "db", "refresh": true}}'
        #server_certificate: bytes = self.run_command_on_the_container(f"echo quit | openssl s_client -showcerts -servername {self.virtual_ip_address} -connect {self.virtual_ip_address}:443 > /app/server_certificate.pem")
        #assert self.find_in_the_output(server_certificate, b'"DONE"'), f'Could not get certificate from the server at {self.virtual_ip_address}:443'
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with socket.create_connection((self.virtual_ip_address, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=self.virtual_ip_address) as ssl_sock:
                with open("/opt/superset-testing/server_certificate.pem", "wb") as f:
                    f.write(ssl.DER_cert_to_PEM_cert(ssl_sock.getpeercert(binary_form=True)).encode())
        self.copy_file_to_the_container(host_filepath='/opt/superset-testing/server_certificate.pem', container_dirpath='/app')
        api_login_output: bytes = self.run_command_on_the_container(f"curl --cacert /app/server_certificate.pem --silent --url {self.api_default_url}/security/login --header '{headers}' --data '{payload}'")
        assert not self.find_in_the_output(api_login_output, b'"message"'), f'Could not log in to the Superset API {api_login_output}'
        return self.decode_command_output(api_login_output).get("access_token")

    @data_structures.Overlay.single_sign_on
    def login_to_superset(self) -> dict[str, str] | AssertionError:
        csrf_login_request: bytes = self.run_command_on_the_container(f"curl --cacert /app/server_certificate.pem --include --url {self.api_default_url}/security/csrf_token/ --header '{self.api_authorization_header}'")
        assert not self.find_in_the_output(csrf_login_request, b'"msg"'), f'Could not pass login request {csrf_login_request}'
        session_request_cookie: str = self.extract_session_cookie(csrf_login_request)
        csrf_token: str = json.loads(csrf_login_request.decode('utf-8').split('\r\n\r\n')[1]).get("result")
        superset_login_request: bytes = self.run_command_on_the_container(f"curl --location --cacert /app/server_certificate.pem --include --url https://{self.virtual_ip_address}/login/ --header 'Cookie: session={session_request_cookie}' --data 'csrf_token={csrf_token}'")
        assert not self.find_in_the_output(superset_login_request, b'Redirecting...'), f'Invalid login request to Superset. Could not get a response from the server. Check if it is possible to log in to the server manually.'
        superset_login_session_cookie: str = self.extract_session_cookie(superset_login_request)
        return {
            "csrf_token": csrf_token,
            "session_token": superset_login_session_cookie
        }

    @data_structures.Overlay.post_init_hook
    def status_database(self) -> None | AssertionError:
        with open('/opt/superset-cluster/mysql-mgmt/mysql_superset_password', 'r') as mysql_superset_password:
            payload: str = f'{{"database_name": "MySQL", "sqlalchemy_uri": "mysql+mysqlconnector://superset:{mysql_superset_password.read().strip()}@{self.virtual_ip_address}:6446/superset", "impersonate_user": false}}'
            test_database_connection: bytes = self.run_command_on_the_container(f"curl --location --cacert /app/server_certificate.pem --silent {self.api_default_url}/database/test_connection/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_csrf_header}' --header '{self.api_session_header}' --header 'Referer: https://{self.virtual_ip_address}' --data '{payload}'")
            assert self.find_in_the_output(test_database_connection, b'{"message":"OK"}'), f'Could not connect to the superset database on {self.virtual_ip_address} port 6446, the database is either down or not configured according to the given SQL Alchemy URI, {test_database_connection}'

    @data_structures.Overlay.post_init_hook
    def status_swarm(self) -> None | AssertionError:
        swarm_info = self.info()['Swarm']
        assert swarm_info['LocalNodeState'] == 'active', 'The Swarm node has not been activated'
        assert swarm_info['ControlAvailable'] is True, f'The testing localhost is supposed to be a Swarm manager, but it is not'

    def run_query(self) -> float | AssertionError:
        payload: str = f'{{"database_id": 1, "runAsync": true, "sql": "SELECT * FROM superset.logs;"}}'
        sqllab_run_query: bytes = self.run_command_on_the_container(f"curl --location --cacert /app/server_certificate.pem --silent {self.api_default_url}/sqllab/execute/ --header 'Content-Type: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header '{self.api_csrf_header}' --header 'Referer: https://{self.virtual_ip_address}' --data '{payload}'")
        assert not self.find_in_the_output(sqllab_run_query, b'"msg"'), f'SQL query execution failed with the following message: {sqllab_run_query}'
        assert not self.find_in_the_output(sqllab_run_query, b'"message"'), f'Could not execute query on: superset'
        dttm_time_query_identifier: float = self.decode_command_output(sqllab_run_query).get("query").get("startDttm")
        return dttm_time_query_identifier
    
    def get_query_results(self, dttm_time_query_identifier: float):
        time.sleep(22)  # state refreshing
        query_result: dict = self.decode_command_output(
            self.run_command_on_the_container(f"curl --location --cacert /app/server_certificate.pem --silent '{self.api_default_url}/query/updated_since?q=(last_updated_ms:{dttm_time_query_identifier})' --header 'Accept: application/json' --header '{self.api_authorization_header}' --header '{self.api_session_header}' --header 'Referer: https://{self.virtual_ip_address}' --header '{self.api_csrf_header}'")
        ) 
        assert query_result.get("result")[0]['state'] == 'success', f'Could not find query state or returned unsuccessful: {query_result}'
        results_key: str = f"superset_results{query_result.get('result')[0]['resultsKey']}"
        assert self.redis.fetch_query_result(results_key), f'Query result with the {results_key} key can not be found in Redis'
        assert self.celery.find_processed_queries(), 'Query seems to be processed outside Celery worker'
