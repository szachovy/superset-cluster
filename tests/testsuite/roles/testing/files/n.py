from ctypes import *

class Sockaddr(Structure):
    _fields_ = [('sa_family', c_ushort), ('sa_data', c_char * 14)]

class Ifa_Ifu(Union):
    _fields_ = [('ifu_broadaddr', POINTER(Sockaddr)),
                ('ifu_dstaddr', POINTER(Sockaddr))]

class struct_sockaddr_in(Structure):
    _fields_ = [
        ('sin_family', c_ushort),
        ('sin_port', c_uint16),
        ('sin_addr', c_byte * 4)]

class Ifaddrs(Structure):
    pass

Ifaddrs._fields_ = [('ifa_next', POINTER(Ifaddrs)), ('ifa_name', c_char_p),
                    ('ifa_flags', c_uint), ('ifa_addr', POINTER(Sockaddr)),
                    ('ifa_netmask', POINTER(Sockaddr)), ('ifa_ifu', Ifa_Ifu),
                    ('ifa_data', c_void_p)]

from socket import AF_INET, AF_INET6, inet_ntop
def get_interfaces():
    libc = CDLL('libc.so.6')
    libc.getifaddrs.restype = c_int
    ifaddr_p = pointer(Ifaddrs())
    ret = libc.getifaddrs(pointer((ifaddr_p)))
    interfaces = set()
    head = ifaddr_p
    while ifaddr_p:
        
        addr = inet_ntop(AF_INET, cast(pointer(ifaddr_p.contents), POINTER(struct_sockaddr_in)).contents.sin_addr)
        interfaces.add(ifaddr_p.contents.ifa_name)
        ifaddr_p = ifaddr_p.contents.ifa_next
    libc.freeifaddrs(head) 
    return interfaces

if __name__ == "__main__":
    print(get_interfaces())