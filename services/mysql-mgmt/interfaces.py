"""
Network Interface Management Module

This module provides structures and functions to interface with system-level
networking information, specifically to retrieve and manipulate details about
network interfaces using the `ctypes` library.

The main functionality includes:
- Struct definitions for representing socket addresses, socket interfaces,
  and network interfaces, mapped to their C counterparts for system compatibility.
- A `network_interfaces` function to obtain the IP address associated with a specified
  network interface name by accessing system-level network configuration data.

Classes:
--------
- `socket_address`: Represents a generic socket address structure for low-level
  network communications.
- `socket_interface`: Represents a socket interface structure with fields for
  family, port, and IP address.
- `network_interface_structure`: Represents the structure of a network interface
  entry, holding pointers to interface name, address, and other related fields.

Functions:
----------
- `network_interfaces(network_interface: str) -> str`: Retrieves the IP address
  for a given network interface name. Uses system-level C functions to access
  network interface data directly.

Example Usage:
--------------
To run the module and retrieve the IP address of a specified network interface
from the environment variable `VIRTUAL_NETWORK_INTERFACE`:

```bash
export VIRTUAL_NETWORK_INTERFACE=eth0  # Replace 'eth0' with your interface name
python module_name.py
"""

# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name

import ctypes
import ctypes.util
import os
import socket


class socket_address(ctypes.Structure):
    _fields_ = [
        ("socket_address_family", ctypes.c_ushort),
        ("socket_address_code", ctypes.c_byte * 14)
    ]


class socket_interface(ctypes.Structure):
    _fields_ = [
        ("socket_interface_family", ctypes.c_ushort),
        ("socket_interface_port", ctypes.c_uint16),
        ("socket_interface_address", ctypes.c_byte * 4)
    ]


class network_interface_structure(ctypes.Structure):
    pass


network_interface_structure._fields_ = [  # pylint: disable=protected-access
    ("next_network_interface", ctypes.POINTER(network_interface_structure)),
    ("network_interface_name", ctypes.c_char_p),
    ("network_interface_flags", ctypes.c_uint),
    ("network_interface_address", ctypes.POINTER(socket_address)),
    ("network_interface_mask", ctypes.POINTER(socket_address)),
    ("network_interface_data", ctypes.c_void_p)
]


def network_interfaces(network_interface: str) -> str:
    clib = ctypes.CDLL(ctypes.util.find_library("c"))
    interfaces = ctypes.POINTER(network_interface_structure)()
    if clib.getifaddrs(ctypes.pointer(interfaces)) == 0:
        current_interface: network_interface_structure = interfaces.contents
        while True:
            if current_interface.network_interface_name == network_interface.encode() \
                   and current_interface.network_interface_data:
                if current_interface.network_interface_address.contents.socket_address_family == 2:
                    return socket.inet_ntop(
                        socket.AF_INET,
                        ctypes.cast(
                            ctypes.pointer(current_interface.network_interface_address.contents),
                            ctypes.POINTER(socket_interface)
                        ).contents.socket_interface_address
                    )
            if not current_interface.next_network_interface:
                clib.freeifaddrs(interfaces)
                raise StopIteration(f"Provided network interface {network_interface} not found")
            current_interface = current_interface.next_network_interface.contents
    raise ValueError(
        f"Network interface {network_interface} cannot be adjusted to be set with provided virtual ip address"
    )


if __name__ == "__main__":
    print(network_interfaces(network_interface=os.environ['VIRTUAL_NETWORK_INTERFACE']))
