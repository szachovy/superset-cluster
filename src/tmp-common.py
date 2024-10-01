# abstract base class
class Remote():
    pass # paramiko ssh, run_command something like in container_connection.py
class Certificates:
    def ca_key():
        return ca_key
    def ca_certificate():
        return ca_certificate

# tmp    
# superset_cluster_key=$(ssh superset@${primary_node} "openssl genpkey -algorithm RSA -out /dev/stdout")
# superset_cluster_csr=$(ssh superset@${primary_node} "openssl req -new -key <(printf '%s\n' '${superset_cluster_key}') -out /dev/stdout -subj '/CN=${virtual_ip_address}'")
# superset_cluster_cert=$(ssh superset@${primary_node} "openssl x509 -in <(printf '%s\n' '${superset_cluster_csr}') -CA <(printf '%s\n' '${ca_certificate}') -CAkey <(printf '%s\n' '${ca_key}') -CAcreateserial -out /dev/stdout -req -days 365")
