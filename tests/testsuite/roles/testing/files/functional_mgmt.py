
import requests
import container
import decorators


class MgmtNodeFunctionalTests(container.ContainerConnection, metaclass=decorators.Overlay):
    def __init__(self, virtual_ip_address: str, node_prefix: str, after_disaster: bool) -> None:
        super().__init__(container='mysql-mgmt')
        self.copy_file_to_the_container(host_filepath='/opt/superset-cluster/mysql-mgmt/.mylogin.cnf', container_dirpath='/home/superset')
        self.virtual_ip_address: str = virtual_ip_address
        self.mgmt_primary_node: str = f"{node_prefix}-0"
        self.mgmt_secondary_node: str = f"{node_prefix}-1"
        self.mysql_primary_node: str = f"{node_prefix}-2"
        self.mysql_secondary_nodes: list = [f"{node_prefix}-3", f"{node_prefix}-4"]
        self.after_disaster: bool = after_disaster

    @decorators.Overlay.run_selected_methods_once
    def status_cluster(self):
        command: str = f"mysqlsh --login-path={self.mysql_secondary_nodes[0]} --interactive --execute=\"dba.getCluster(\'superset\').status();\""
        cluster_status_output: bytes = self.run_command_on_the_container(command)
        if self.after_disaster:
            assert self.find_in_the_output(cluster_status_output, b'"status": "OK_NO_TOLERANCE_PARTIAL"'), f'The MySQL InnoDB cluster desired state after disaster is unappropriate\nCommand: {command}\nReturned: {cluster_status_output}'
        else:
            assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), f'The MySQL InnoDB cluster is not online or can not tolerate failures\nCommand: {command}\nReturned: {cluster_status_output}'
            assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), f'One primary instance is allowed for a given MySQL InnoDB cluster settings\nCommand: {command}\nReturned: {cluster_status_output}'

    @decorators.Overlay.run_selected_methods_once
    def status_routers(self):
        command: str = f"mysqlsh --login-path={self.mysql_secondary_nodes[0]} --interactive --execute=\"dba.getCluster(\'superset\').listRouters();\""
        routers_status_output: bytes = self.run_command_on_the_container(command)
        assert (self.find_in_the_output(routers_status_output, f'{self.mgmt_primary_node}'.encode()) and self.find_in_the_output(routers_status_output, f'{self.mgmt_secondary_node}'.encode())), f'MySQL Mgmt routers are offline or not attached, expected {self.mgmt_primary_node} and {self.mgmt_secondary_node} to be visible from the superset cluster\nCommand: {command}\Returned: {routers_status_output}'

    def check_after_disaster(self):
        with open('/opt/superset-cluster/mysql-mgmt/mysql_superset_password', 'r') as mysql_superset_password:
            try:
                command: str = f"mysqlsh --interactive --uri superset:{mysql_superset_password.read().strip()}@{self.virtual_ip_address}:6446 --sql --execute \"SELECT @@hostname;\""
                new_mysql_primary_node: bytes = self.run_command_on_the_container(command)
                if not self.find_in_the_output(new_mysql_primary_node, self.mysql_secondary_nodes[0].encode('utf-8')):
                    if not self.find_in_the_output(new_mysql_primary_node, self.mysql_secondary_nodes[1].encode('utf-8')):
                        raise AssertionError(f'After stopping {self.mysql_primary_node}, one of {self.mysql_secondary_nodes} was expected to be selected as the new primary. Selection process failed\nCommand: {command} \nReturned: {new_mysql_primary_node}')
            except requests.exceptions.RequestException:
                raise AssertionError(f'After stopping {self.mgmt_primary_node} {self.mgmt_secondary_node} was expected to be selected as the new primary. Selection process failed\nCommand: {command} \nReturned: {new_mysql_primary_node}')
