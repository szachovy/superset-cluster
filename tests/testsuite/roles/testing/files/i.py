from socket import AF_INET, AF_INET6, inet_ntop
from ctypes import (
    Structure, Union, POINTER, 
    pointer, get_errno, cast,
    c_ushort, c_byte, c_void_p, c_char_p, c_uint, c_int, c_uint16, c_uint32
)
import ctypes.util
import ctypes

class struct_sockaddr(Structure):
     _fields_ = [
        ('sa_family', c_ushort),
        ('sa_data', c_byte * 14),]

class struct_sockaddr_in(Structure):
    _fields_ = [
        ('sin_family', c_ushort),
        ('sin_port', c_uint16),
        ('sin_addr', c_byte * 4)]

class struct_ifaddrs(Structure):
    pass

struct_ifaddrs._fields_ = [
    ('ifa_next', POINTER(struct_ifaddrs)),
    ('ifa_name', c_char_p),
    ('ifa_flags', c_uint),
    ('ifa_addr', POINTER(struct_sockaddr)),
    ('ifa_netmask', POINTER(struct_sockaddr)),
    ('ifa_data', c_void_p),]

# NETWORK_INTERFACE = 'lo'
# NETWORK_INTERFACE = 'wlp4s0'
# NETWORK_INTERFACE = 'docker0'
NETWORK_INTERFACE = 'tun0'

def get_network_interfaces():
    libc = ctypes.CDLL(ctypes.util.find_library('c'))
    ifap = POINTER(struct_ifaddrs)()
    if libc.getifaddrs(pointer(ifap)) == 0:
        while True:
            if ifap.contents.ifa_name == NETWORK_INTERFACE.encode() and ifap.contents.ifa_data:
                if ifap.contents.ifa_addr.contents.sa_family == 2:
                    addr = inet_ntop(AF_INET, cast(pointer(ifap.contents.ifa_addr.contents), POINTER(struct_sockaddr_in)).contents.sin_addr)
                    print(ifap.contents.ifa_name)
                    print(addr)
            if not ifap.contents.ifa_next:
                break
            ifap.contents = ifap.contents.ifa_next.contents
    # libc.freeifaddrs(ifap)
    exit(0)

if __name__ == '__main__':
    print([str(ni) for ni in get_network_interfaces()])

# ["b'lo' [index=1, IPv4=127.0.0.1, IPv6=::1]", "b'enx00e04c682c97' [index=3, IPv4=None, IPv6=None]", "b'wwan0' [index=4, IPv4=None, IPv6=None]", "b'wlp4s0' [index=5, IPv4=10.0.0.111, IPv6=fe80::ac02:e6e7:e8d9:60d5]", "b'docker0' [index=6, IPv4=172.17.0.1, IPv6=None]", "b'br-982866f4f233' [index=7, IPv4=172.16.0.1, IPv6=None]", "b'docker_gwbridge' [index=8, IPv4=172.20.0.1, IPv6=None]", "b'br-77cc835a2444' [index=10, IPv4=172.18.0.1, IPv6=fe80::42:b6ff:fed6:d3c4]", "b'veth7d6d4f8' [index=12, IPv4=None, IPv6=fe80::4806:cfff:fef7:7655]", "b'veth189edba' [index=14, IPv4=None, IPv6=fe80::184b:37ff:fe96:b9ae]", "b'veth52bd0c8' [index=16, IPv4=None, IPv6=fe80::cc87:e7ff:fe96:a8e6]", "b'veth16f8ae2' [index=18, IPv4=None, IPv6=fe80::44b5:96ff:feab:8bbd]", "b'veth8be41de' [index=20, IPv4=None, IPv6=fe80::d07b:60ff:fec0:6578]", "b'tun0' [index=21, IPv4=10.100.210.218, IPv6=fe80::59dd:f73:1c0a:b5d0]"]
