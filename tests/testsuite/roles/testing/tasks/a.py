import socket
for node in {{ nodes }}:
    socket.gethostbyname("{{ node-prefix }}-{node}")