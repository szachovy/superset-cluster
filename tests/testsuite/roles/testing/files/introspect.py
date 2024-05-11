
import os  # I think it's better to use subprocess for this. but quick code for example
import socket

NODES = 5
NODE_PREFIX = "node"
NETWORK_INTERFACE = "eth0"

def check_services():
    if not os.system('service ssh status'):
        raise Exception()
    if not os.system('service docker status'):
        raise Exception()

def check_dns():
    for node in NODES:
        socket.gethostbyname(f"{NODE_PREFIX}-{node}")

def check_network_interface():
    import src.interfaces
    src.interfaces.network_interfaces(NETWORK_INTERFACE=NETWORK_INTERFACE)