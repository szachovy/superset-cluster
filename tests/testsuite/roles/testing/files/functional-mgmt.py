
import argparse
import time
import data_structures


class ArgumentParser:
    def __init__(self) -> None:
        self.parser: argparse.ArgumentParser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        self.parser.add_argument('--node-prefix', type=str)
        self.parser.add_argument('--mgmt-hostname', type=str)
        self.parser.add_argument('--mysql-user', type=str)
        self.parser.add_argument('--mysql-password', type=str)

    def parse_arguments(self) -> argparse.Namespace:
        return self.parser.parse_args()


class MgmtNodeFunctionalTests(data_structures.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self) -> None:
        super().__init__(node=self.arguments.mgmt_hostname)
        self.arguments: argparse.Namespace = ArgumentParser().parse_arguments()
        self.mgmt_primary_node: str = f"{self.node_prefix}-0"
        self.mgmt_secondary_node: str = f"{self.node_prefix}-10"
        self.mysql_primary_node: str = f"{self.node_prefix}-1"
        self.mysql_secondary_nodes: list = [f"{self.node_prefix}-2", f"{self.node_prefix}-3"]
        self.mysql_node_disaster_delay: int = 300
        self.mgmt_node_disaster_delay: int = 12

    @data_structures.Overlay.post_init_hook
    def status_cluster(self):
        cluster_status_output: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri {self.arguments.mysql_user}:{self.arguments.mysql_password}@{self.arguments.node_prefix}-0:6446 --execute \"dba.getCluster(\'cluster\').status();\"")
        assert self.find_in_the_output(cluster_status_output, b'"status": "OK"'), 'The MySQL InnoDB cluster is not online or can not tolerate failures'
        assert self.find_in_the_output(cluster_status_output, b'"topologyMode": "Single-Primary"'), 'One primary instance is allowed for a given MySQL InnoDB cluster settings'

    @data_structures.Overlay.post_init_hook
    def status_routers(self):
        routers_status_output: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri {self.arguments.mysql_user}:{self.arguments.mysql_password}@{self.arguments.node_prefix}-0:6446 --execute \"dba.getCluster(\'cluster\').listRouters();\"")

    @data_structures.Overlay.post_init_hook
    def status_swarm(self):
        swarm_status_output: bytes = self.run_command_on_the_container("docker info")
        assert self.find_in_the_output(swarm_status_output, b'Swarm: active'), 'The Swarm node has not been activated'
        assert self.find_in_the_output(swarm_status_output, b'Is Manager: false'), f'The {self.arguments.node_prefix}-0 is not supposed to be a Swarm manager, but it is'

    def check_mysql_after_disaster(self):
        self.stop_node(self.mysql_primary_node)
        time.sleep(self.mysql_node_disaster_delay)
        new_mysql_primary_node: bytes = self.run_command_on_the_container(f"mysqlsh --interactive --uri {self.arguments.mysql_user}:{self.arguments.mysql_password}@{self.arguments.node_prefix}-0:6446 --sql --execute \"SELECT @@hostname;\"")
        assert self.find_in_the_output(new_mysql_primary_node, self.mysql_secondary_nodes[0].encode('utf-8')), f'After stopping {self.mysql_primary_node}, {self.mysql_secondary_nodes[0]} was expected to be selected as the new primary in a round-robin fashion. Selection process failed'

    def check_router_after_disaster(self):
        # self.stop_node(self.mgmt_primary_node)
        # time.sleep(self.mgmt_node_disaster_delay)
        # new_self.mgmt_primary_node: bytes = ...
        # assert self.find_in_the_output(new_self.mgmt_primary_node, ...), f'After stopping {self.mgmt_primary_node}, {self.mgmt_secondary_node: str }  was expected to be selected as the new primary in a round-robin fashion. Selection process failed'
        pass

mgmt_functional = MgmtNodeFunctionalTests()
mgmt_functional.check_mysql_after_disaster()
mgmt_functional.check_router_after_disaster()