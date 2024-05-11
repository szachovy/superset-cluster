
import ctypes
import ctypes.util


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

class network_interface(ctypes.Structure):
    pass
