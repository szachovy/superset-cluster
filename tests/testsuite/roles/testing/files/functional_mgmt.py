
import requests
import container_connection
import data_structures


class MgmtNodeFunctionalTests(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, mgmt_hostname: str, virtual_ip_address: str, node_prefix: str, after_disaster: bool) -> None:
        super().__init__(node=mgmt_hostname)
        self.copy_mysql_login_configuration_to_the_container()
        self.virtual_ip_address: str = virtual_ip_address
        self.mgmt_primary_node: str = f"{node_prefix}-0"
        self.mgmt_secondary_node: str = f"{node_prefix}-5"
        self.mysql_primary_node: str = f"{node_prefix}-1"
        self.mysql_secondary_nodes: list = [f"{node_prefix}-2", f"{node_prefix}-3"]
        self.after_disaster: bool = after_disaster

    @data_structures.Overlay.post_init_hook
    def status_cluster(self):
        cluster_status_output: bytes = self.run_command_on_the_container(f"mysqlsh --login-path={self.mysql_secondary_nodes[0]} --interactive --execute=\"dba.getCluster(\'superset\').status();\"")
        if self.after_disaster:
            assert self.find_in_the_output(cluster_status_output, b'"status": "OK_NO_TOLERANCE_PARTIAL"'), 'The MySQL InnoDB cluster desired state after disaster is unappropriate'
        else:
            assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), f'The MySQL InnoDB cluster is not online or can not tolerate failures: {cluster_status_output}'
            assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), 'One primary instance is allowed for a given MySQL InnoDB cluster settings'

    @data_structures.Overlay.post_init_hook
    def status_routers(self):
        routers_status_output: bytes = self.run_command_on_the_container(f"mysqlsh --login-path={self.mysql_secondary_nodes[0]} --interactive --execute=\"dba.getCluster(\'superset\').listRouters();\"")
        assert (self.find_in_the_output(routers_status_output, f'{self.mgmt_primary_node}'.encode()) and self.find_in_the_output(routers_status_output, f'{self.mgmt_secondary_node}'.encode())), f'MySQL Mgmt routers are offline or not attached, expected {self.mgmt_primary_node} and {self.mgmt_secondary_node} to be visible from the superset cluster'

    @data_structures.Overlay.post_init_hook
    def status_swarm(self):
        if not self.after_disaster:
            swarm_info = self.info()['Swarm']
            assert swarm_info['LocalNodeState'] == 'active', 'The Swarm node has not been activated'
            assert swarm_info['ControlAvailable'] is False, f'The {self.virtual_ip_address} is not supposed to be a Swarm manager, but it is'

    def check_after_disaster(self):
        try:
            new_mysql_primary_node: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri superset:cluster@{self.virtual_ip_address}:6446 --sql --execute \"SELECT @@hostname;\"")
            if not self.find_in_the_output(new_mysql_primary_node, self.mysql_secondary_nodes[0].encode('utf-8')):
                if not self.find_in_the_output(new_mysql_primary_node, self.mysql_secondary_nodes[1].encode('utf-8')):
                    raise AssertionError(f'After stopping {self.mysql_primary_node}, one of {self.mysql_secondary_nodes} was expected to be selected as the new primary. Selection process failed with the output: {new_mysql_primary_node}')
        except requests.exceptions.RequestException:
            raise AssertionError(f'After stopping {self.mgmt_primary_node} {self.mgmt_secondary_node} was expected to be selected as the new primary. Selection process failed')
