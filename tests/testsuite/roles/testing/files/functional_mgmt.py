
import time

import data_structures
import container_connection
import retry

class MgmtNodeFunctionalTests(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self, mgmt_hostname: str, mysql_user: str, mysql_password: str, node_prefix: str, after_disaster: bool) -> None:
        super().__init__(node=mgmt_hostname)
        self.mysql_user: str = mysql_user
        self.mysql_password: str = mysql_password
        self.mgmt_primary_node: str = f"{node_prefix}-0"
        self.mgmt_secondary_node: str = f"{node_prefix}-10"
        self.mysql_primary_node: str = f"{node_prefix}-1"
        self.mysql_secondary_nodes: list = [f"{node_prefix}-2", f"{node_prefix}-3"]
        self.after_disaster: bool = after_disaster
        if after_disaster:
            self.mysql_node_disaster_delay: int = 600
            self.counter = 0
            self.mgmt_node_disaster_delay: int = 12

    @data_structures.Overlay.post_init_hook
    def status_cluster(self):
        if self.after_disaster:
            cluster_status_output: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri {self.mysql_user}:{self.mysql_password}@{self.mgmt_primary_node}:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
            assert self.find_in_the_output(cluster_status_output, b'"status": "OK_NO_TOLERANCE_PARTIAL"'), 'The MySQL InnoDB cluster desired state after disaster is unappropriate'
        else:
            cluster_status_output: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri {self.mysql_user}:{self.mysql_password}@{self.mgmt_primary_node}:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
            assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), f'The MySQL InnoDB cluster is not online or can not tolerate failures: {cluster_status_output}'
            assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), 'One primary instance is allowed for a given MySQL InnoDB cluster settings'

    @data_structures.Overlay.post_init_hook
    def status_routers(self):
        if self.after_disaster:
            pass
        else:
            routers_status_output: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri {self.mysql_user}:{self.mysql_password}@{self.mgmt_primary_node}:6446 --execute \"dba.getCluster(\'cluster\').listRouters();\"")

    @data_structures.Overlay.post_init_hook
    def status_swarm(self):
        if not self.after_disaster:
            swarm_info = self.info()['Swarm']
            assert swarm_info['LocalNodeState'] == 'active', 'The Swarm node has not been activated'
            assert swarm_info['ControlAvailable'] is False, f'The {self.mgmt_primary_node} is not supposed to be a Swarm manager, but it is'

    def check_mysql_after_disaster(self):
        if self.after_disaster:
            # time.sleep(self.mysql_node_disaster_delay)
            new_mysql_primary_node: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri {self.mysql_user}:{self.mysql_password}@{self.mgmt_primary_node}:6446 --sql --execute \"SELECT @@hostname;\"")
            if not self.find_in_the_output(new_mysql_primary_node, self.mysql_secondary_nodes[0].encode('utf-8')):
                if not self.find_in_the_output(new_mysql_primary_node, self.mysql_secondary_nodes[1].encode('utf-8')):
                    raise AssertionError(f'After stopping {self.mysql_primary_node}, one of {self.mysql_secondary_nodes} was expected to be selected as the new primary. Selection process failed with the output: {new_mysql_primary_node}')

    def check_router_after_disaster(self):
        if self.after_disaster:
            # time.sleep(self.mgmt_node_disaster_delay)
            # new_self.mgmt_primary_node: bytes = ...
            # assert self.find_in_the_output(new_self.mgmt_primary_node, ...), f'After stopping {self.mgmt_primary_node}, {self.mgmt_secondary_node: str }  was expected to be selected as the new primary in a round-robin fashion. Selection process failed'
            pass
