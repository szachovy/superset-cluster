
import ctypes
import ctypes.util
import ipaddress
import os
import socket


class socket_address(ctypes.Structure):
    _fields_ = [
        ('socket_address_family', ctypes.c_ushort),
        ('socket_address_code', ctypes.c_byte * 14)
    ]


class socket_interface(ctypes.Structure):
    _fields_ = [
        ('socket_interface_family', ctypes.c_ushort),
        ('socket_interface_port', ctypes.c_uint16),
        ('socket_interface_address', ctypes.c_byte * 4)
    ]


class network_interface_structure(ctypes.Structure):
    pass

network_interface_structure._fields_ = [
    ('next_network_interface', ctypes.POINTER(network_interface_structure)),
    ('network_interface_name', ctypes.c_char_p),
    ('network_interface_flags', ctypes.c_uint),
    ('network_interface_address', ctypes.POINTER(socket_address)),
    ('network_interface_mask', ctypes.POINTER(socket_address)),
    ('network_interface_data', ctypes.c_void_p)
]

def network_interfaces(network_interface: str) -> str | StopIteration:
    clib: ctypes.CDLL = ctypes.CDLL(ctypes.util.find_library('c'))
    network_interfaces: ctypes.POINTER = ctypes.POINTER(network_interface_structure)()
    if clib.getifaddrs(ctypes.pointer(network_interfaces)) == 0:
        current_interface: network_interface_structure = network_interfaces.contents
        while True:
            if current_interface.network_interface_name == network_interface.encode() and current_interface.network_interface_data:
                if current_interface.network_interface_address.contents.socket_address_family == 2:
                    return socket.inet_ntop(socket.AF_INET,
                                            ctypes.cast(ctypes.pointer(current_interface.network_interface_address.contents),
                                                        ctypes.POINTER(socket_interface)
                                                ).contents.socket_interface_address
                                            )
            if not current_interface.next_network_interface:
                clib.freeifaddrs(network_interfaces)
                raise StopIteration(f'Provided network interface {network_interface} not found.')
            current_interface = current_interface.next_network_interface.contents


def virtual_network(virtual_ip_address: str, virtual_network_mask: str) -> str:
    return ipaddress.IPv4Interface(f"{virtual_ip_address}/{virtual_network_mask}").network

if __name__ == "__main__":
    print(network_interfaces(network_interface=os.environ['VIRTUAL_NETWORK_INTERFACE']))