import sys
import re
import socket

import data_structures


if len(sys.argv) != 6:
    print("Error: Invalid form of arguments provided.")
    sys.exit(1)


@data_structures.Overlay.run_all_methods
class ArgumentParser:
    def validate_virtual_ip_address(self) -> None:
        try:
            socket.inet_aton(sys.argv[1])
        except socket.error:
            raise ValueError('Invalid virtual-ip-address provided.') 
        self.virtual_ip_address = sys.argv[1]

    def validate_virtual_network_mask(self) -> None:
        try:
            if 0 <= int(sys.argv[3]) <= 32:
                self.virtual_network_mask = sys.argv[3] 
        except ValueError:
            raise ValueError('Invalid virtual-network-mask provided.')

    def validate_virtual_network_interface(self) -> None:
        if re.match(r"^[a-zA-Z0-9_-]+$", sys.argv[2]) is not None:
            self.virtual_network_interface = sys.argv[2]
        else:
            raise ValueError('Invalid virtual-network-interface provided.')

    def validate_nodes(self) -> None:
        self.mgmt_nodes = []
        self.mysql_nodes = []

        def validate_hostname(hostname: str) -> str:
            """(RFC 1123 compliance)."""
            allowed_characters = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
            if not ((len(hostname) > 255) or ("." in hostname)):
                if all(allowed_characters.match(x) for x in hostname):
                    return hostname
            raise ValueError(f'Invalid node hostname provided.')
        
        for mgmt_node in (node for mgmt_node in sys.argv[4].split(',') for node in mgmt_node.split(' ')):
            self.mgmt_nodes.append(validate_hostname(mgmt_node))
        for mysql_node in (node for mysql_node in sys.argv[5].split(',') for node in mysql_node.split(' ')):
            self.mysql_nodes.append(validate_hostname(mysql_node))

class OpenSSL():
    pass

class Controller(ArgumentParser):
    def __init__(self) -> None:
        super().__init__()
        print(self.virtual_network_mask)
        print(self.virtual_ip_address)
        print(self.virtual_network_interface)
        print(self.mgmt_nodes)
        print(self.mysql_nodes)


if __name__ == "__main__":
    Controller()