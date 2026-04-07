# Architecture

This document describes the architecture of superset-cluster, a resilient Business Intelligence deployment tool
that orchestrates [Apache Superset](https://superset.apache.org/) across a multi-node cluster with
[MySQL InnoDB Cluster](https://dev.mysql.com/doc/refman/8.0/en/mysql-innodb-cluster-introduction.html).

For details in each particular topic, follow:
* [PERFORMANCE.md](./PERFORMANCE.md)
* [SECURITY.md](./SECURITY.md)
* [RELIABILITY.md](./RELIABILITY.md)

## Cluster Overview

![Architecture](arch.svg)

The cluster is composed of five nodes organized into two roles:

| Role | Number of Nodes | Components |
|------|-----------------|------------|
| Management | 2 | MySQL Router, Keepalived (VRRP), Superset (Docker Swarm service) |
| MySQL | 3 | MySQL Server 8.0 (InnoDB Cluster, single-primary mode) |

A floating Virtual IP address (VIP) is shared between the two management nodes using VRRP. External clients
connect to the cluster exclusively through `https://<VIP>:443`. Internal communication between components uses
host networking and the Docker Swarm overlay network.

## Components

### MySQL InnoDB Cluster

Three MySQL 8.0 instances form an
[InnoDB Cluster](https://dev.mysql.com/doc/refman/8.0/en/mysql-innodb-cluster-introduction.html) in single-primary
mode. One node accepts writes (the primary), while the other two replicate data and serve as secondaries for
automatic failover. Each MySQL server container is based on `mysql:8.0-debian`, runs with host networking, and
mounts its TLS certificates and root password from the host filesystem. A custom seccomp profile restricts
dangerous syscalls.

### Management Nodes

[MySQL Router](https://dev.mysql.com/doc/mysql-router/8.0/en/) runs on each management node inside the
`mysql-mgmt` container. It is bootstrapped against the InnoDB Cluster primary and automatically discovers the
cluster topology. Clients connect to port **6446** (read-write) which the router forwards to the current
primary MySQL node.

[Keepalived](https://www.keepalived.org/) provides Virtual Router Redundancy Protocol (VRRP) between the two
management nodes. The first management node starts as `MASTER`, and the second as `BACKUP`. It tracks the
`mysqlrouter` process to trigger failover if the router goes down.

### Redis

A Redis container runs on the Docker Swarm overlay network (`superset-network`). It serves two purposes:

1. **Celery broker** (`redis://redis:6379/0`): distributes asynchronous task messages.
2. **Results backend**: stores SQL Lab query results and filter state caches.

Redis is deployed as a standard Docker container (not a Swarm service) attached to the overlay network.

### Apache Superset

Superset is deployed as a **Docker Swarm service** with `maxreplicas=1`, ensuring exactly one instance runs
across the Swarm cluster. The service is attached to the `superset-network` overlay and publishes port 443
via Swarm's VIP-based endpoint spec. Each Superset container runs three processes:

1. **Nginx** (HTTPS reverse proxy on port 443) → forwards to Gunicorn on `localhost:8088`.
2. **Gunicorn** (WSGI server) → runs the Superset web application.
3. **Celery worker** (4 concurrency, prefork pool, fair scheduling) → executes asynchronous SQL queries.

Nginx runs inside each Superset container as a TLS-terminating reverse proxy listening on port 443. It
forwards requests to Gunicorn on `localhost:8088` with proper `X-Forwarded-*` headers. TLS configuration
and security headers are detailed in [SECURITY.md](SECURITY.md).

The entrypoint script tests the database connection, creates the default admin user (`superset`/`cluster`),
runs database migrations (`superset db upgrade`), initializes Superset (`superset init`), and sets up the
MySQL database connection URI automatically.

Secrets (Superset secret key and MySQL password) are provided through Docker Swarm secrets mounted at
`/run/secrets/`.

## Initialization Flow

The cluster is initialized by the `Controller.start_cluster()` method in `src/initialize.py`, which
orchestrates the following sequence:

```text
1. Credential Generation (Controller.credentials)
   ├── Generate CA private key and self-signed CA certificate
   ├── Generate MySQL root password, MySQL superset password, Superset secret key
   ├── For each node (MySQL + management):
   │   └── Generate RSA 2048-bit private key, CSR, and CA-signed certificate
   └── For each management node (additional):
       └── Generate Superset TLS private key, CSR, and CA-signed certificate

2. Start MySQL Servers (Controller.start_mysql_servers)
   └── For each MySQL node: upload service files, certificates, and run container

3. Start MySQL Management — Node 0 as MASTER (Controller.start_mysql_mgmt)
   └── Run Docker Compose (initcontainer → maincontainer):
       initcontainer: configure InnoDB Cluster, create superset user, bootstrap Router, configure Keepalived
       maincontainer: start Keepalived, start MySQL Router

4. Start MySQL Management — Node 1 as BACKUP (Controller.start_mysql_mgmt)

5. Start Superset (Controller.start_superset)
   └── For each management node: initialize Docker Swarm, create overlay network,
       start Redis container, create Superset Swarm service

6. Cleanup — close all SSH and SFTP connections
```

## Remote Execution Model

The controller runs on the user's workstation and communicates with cluster nodes over SSH using
[Paramiko](https://www.paramiko.org/). The `RemoteConnection` class provides:

- **SSH/SFTP connections**: connects as the `superset` user, either directly or through `~/.ssh/config`.
- **Python bytecode execution**: `container.py` source is compiled to `.pyc`, uploaded to the remote node,
  and executed via `python3 /opt/<nonce>.pyc`. This allows running Docker API commands on remote nodes
  without installing additional management software.
- **Directory and file uploads**: recursive SFTP-based uploads of service directories, certificates,
  and passwords.

## Networking

MySQL Server and MySQL Management containers run with `network_mode: host`, sharing the host's network
stack. This enables:

- Direct access to MySQL on port 3306 from other nodes using hostnames.
- Keepalived to manage the VIP directly on the host's network interface.
- MySQL Router to bind to the host's port 6446.

Redis and Superset run on the `superset-network` overlay network, which provides:

- Service discovery: Superset connects to Redis using the hostname `redis`.
- Port publishing: Swarm publishes port 443 on all Swarm nodes via VIP-based routing.

| Port | Protocol | Service | Scope |
|------|----------|---------|-------|
| 443 | HTTPS | Nginx → Superset | External (via VIP) |
| 3306 | MySQL | MySQL Server | Internal (cluster nodes) |
| 6446 | MySQL | MySQL Router (R/W) | Internal (management nodes → VIP) |
| 6379 | Redis | Redis | Internal (overlay network) |
| 8088 | HTTP | Gunicorn | Internal (localhost only) |

## High Availability

If the active management node fails:

1. Keepalived detects the loss via VRRP advertisement timeout (1-second interval).
2. The backup node promotes itself to `MASTER` and acquires the VIP.
3. Gratuitous ARP updates network switches to route traffic to the new master.
4. MySQL Router on the new master continues serving client connections.

If the MySQL primary node fails:

1. InnoDB Cluster Group Replication detects the failure through its consensus protocol.
2. One of the two secondary nodes is automatically elected as the new primary.
3. MySQL Router detects the topology change and redirects read-write traffic to the new primary.
4. The cluster status transitions from `OK` to `OK_NO_TOLERANCE_PARTIAL`, indicating reduced fault
   tolerance.

If the Superset container fails:

Superset runs as a Docker Swarm service with `maxreplicas=1`. Swarm automatically reschedules it on an available manager node. The service connects to MySQL through the
VIP (port 6446), so it is transparent to management node failovers.

For detailed fault tolerance scenarios, health check configuration, and VRRP behavior, see
[RELIABILITY.md](RELIABILITY.md).
