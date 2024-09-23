
import container_connection
import data_structures

class Service(container_connection.ContainerUtilities, metaclass=data_structures.Overlay):
    def __init__(self) -> None:
        super().__init__(container=None)

    @data_structures.Overlay.post_init_hook
    def status_swarm(self) -> None | AssertionError:
        swarm_info = self.info()['Swarm']
        assert swarm_info['LocalNodeState'] == 'active', 'The Swarm node has not been activated'
        assert swarm_info['ControlAvailable'] is True, f'The testing localhost is supposed to be a Swarm manager, but it is not'
        assert swarm_info['Nodes'] == 3, f'The Swarm is expected to consist of 3 nodes instead of {swarm_info["Nodes"]} in the pool.'
