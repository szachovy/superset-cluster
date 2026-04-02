# Architecture

This document describes the architecture of superset-cluster, a resilient Business Intelligence deployment tool
that orchestrates [Apache Superset](https://superset.apache.org/) across a multi-node cluster with
[MySQL InnoDB Cluster](https://dev.mysql.com/doc/refman/8.0/en/mysql-innodb-cluster-introduction.html),
[Redis](https://redis.io/) caching, and automatic failover. For security-related topics, including TLS, credential
management, reliability, and performance, refer to [SECURITY.md](SECURITY.md).

## Cluster Overview

![Architecture](arch.svg)

The cluster is composed of five nodes organized into two roles:

| Role | Nodes | Components |
|------|-------|------------|
| Management | 2 (e.g., `node-0`, `node-1`) | MySQL Router, Keepalived (VRRP), Superset (Docker Swarm service) |
| MySQL | 3 (e.g., `node-2`, `node-3`, `node-4`) | MySQL Server 8.0 (InnoDB Cluster, single-primary mode) |

A floating Virtual IP address (VIP) is shared between the two management nodes using VRRP. External clients connect
to the cluster exclusively through `https://<VIP>:443`. Internal communication between components uses host
networking and the Docker Swarm overlay network.

## Components

### MySQL InnoDB Cluster

Three MySQL 8.0 instances form an
[InnoDB Cluster](https://dev.mysql.com/doc/refman/8.0/en/mysql-innodb-cluster-introduction.html) in single-primary
mode. One node accepts writes (the primary), while the other two replicate data and serve as secondaries for
automatic failover. Key configuration choices in `mysql_config.cnf.tpl`:

- **GTID-based replication** (`gtid_mode=ON`, `enforce_gtid_consistency=ON`) enables consistent failover.
- **`READ-COMMITTED` isolation** avoids gap locking, which is appropriate for the Superset workload.
- **`WRITESET` dependency tracking** allows parallel applier threads on secondaries.
- **Disabled non-InnoDB engines** (`MyISAM`, `BLACKHOLE`, `FEDERATED`, `ARCHIVE`, `MEMORY`) ensures all tables
  participate in cluster replication.
- **SSL required** (`require_secure_transport=ON`) with CA-signed certificates on every node.

Each MySQL server container is based on `mysql:8.0-debian`, runs with host networking, and mounts its TLS
certificates and root password from the host filesystem. A custom seccomp profile restricts the `kill` syscall.

### MySQL Router

[MySQL Router](https://dev.mysql.com/doc/mysql-router/8.0/en/) runs on each management node inside the
`mysql-mgmt` container. It is bootstrapped against the InnoDB Cluster primary and automatically discovers the
cluster topology. Clients connect to port **6446** (read-write) which the router forwards to the current primary
MySQL node. Router is configured with:

- **Client-side SSL required** (`--client-ssl-mode REQUIRED`) with its own TLS certificate.
- **Server-side SSL required** (`--server-ssl-mode REQUIRED`) for connections to MySQL nodes.
- **Unix sockets** (`--conf-use-sockets`) enabled for local performance.

### Keepalived (VRRP)

[Keepalived](https://www.keepalived.org/) provides Virtual Router Redundancy Protocol (VRRP) between the two
management nodes. The first management node starts as `MASTER` (priority 100), and the second as `BACKUP`
(priority 90). Configuration highlights:

- **Virtual Router ID**: 51
- **`nopreempt`**: prevents the original master from reclaiming the VIP after recovery, avoiding unnecessary
  failovers.
- **`track_script`**: monitors the `mysqlrouter` process every second with weight 2, so if MySQL Router goes down,
  the VRRP priority drops and the backup takes over.
- **`track_interface`**: monitors the configured network interface.
- **`garp_master_delay`**: waits 2 seconds before sending gratuitous ARP after becoming master.

### Redis

A Redis container runs on the Docker Swarm overlay network (`superset-network`). It serves two purposes:

1. **Celery broker** (`redis://redis:6379/0`): distributes asynchronous task messages.
2. **Results backend**: stores SQL Lab query results and filter state caches.

Redis is deployed as a standard Docker container (not a Swarm service) attached to the overlay network with an
`always` restart policy and a health check using `redis-cli ping`.

### Apache Superset

Superset is deployed as a **Docker Swarm service** with `maxreplicas=1`, ensuring exactly one instance runs across
the Swarm cluster. The service is attached to the `superset-network` overlay and publishes port 443 via Swarm's
VIP-based endpoint spec. Each Superset container runs three processes:

1. **Nginx** (HTTPS reverse proxy on port 443) → forwards to Gunicorn on `localhost:8088`.
2. **Gunicorn** (WSGI server) → runs the Superset web application.
3. **Celery worker** (4 concurrency, prefork pool, fair scheduling) → executes asynchronous SQL queries.

The entrypoint script tests the database connection, creates the default admin user (`superset`/`cluster`), runs
database migrations (`superset db upgrade`), initializes Superset (`superset init`), and sets up the MySQL database
connection URI automatically.

Secrets (Superset secret key and MySQL password) are provided through Docker Swarm secrets mounted at
`/run/secrets/`.

### Nginx

Nginx runs inside each Superset container as a TLS-terminating reverse proxy. It listens on port 443 with:

- **TLS 1.2 and 1.3** (`ssl_protocols TLSv1.2 TLSv1.3`)
- **Strong cipher suites** (`HIGH:!aNULL:!MD5`)
- **Security headers**: `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`,
  `X-XSS-Protection`, `Referrer-Policy`
- **`server_tokens off`**: hides Nginx version
- **Proxies** requests to Gunicorn at `http://localhost:8088` with proper `X-Forwarded-*` headers

## Initialization Flow

The cluster is initialized by the `Controller.start_cluster()` method in `src/initialize.py`, which orchestrates
the following sequence:

```text
1. Credential Generation (Controller.credentials)
   ├── Generate CA private key and self-signed CA certificate
   ├── Generate MySQL root password (Base64-encoded 16 random bytes)
   ├── Generate MySQL superset password (12 random lowercase ASCII characters)
   ├── Generate Superset secret key (Base64-encoded 42 random bytes)
   ├── For each node (MySQL + management):
   │   ├── Generate RSA 2048-bit private key
   │   ├── Generate CSR with CN=Superset-Cluster-<hostname>
   │   └── Generate CA-signed X.509 certificate (365-day validity)
   └── For each management node (additional):
       ├── Generate RSA 2048-bit private key for Superset TLS
       ├── Generate CSR with CN=<virtual-ip-address>
       └── Generate CA-signed certificate for Superset TLS

2. Start MySQL Servers (Controller.start_mysql_servers)
   └── For each MySQL node:
       ├── Upload services/mysql-server directory
       ├── Upload root password, CA key, CA certificate bundle, node key, node certificate
       └── Run MySQL container with seccomp profile and health checks

3. Start MySQL Management — Node 0 as MASTER (Controller.start_mysql_mgmt)
   ├── Upload services/mysql-mgmt directory
   ├── Upload superset password, .mylogin.cnf, CA key, CA certificate bundle, router key, router certificate
   └── Run Docker Compose (initcontainer then maincontainer):
       ├── initcontainer: configure InnoDB Cluster instances, create cluster, add secondaries,
       │   create superset user, bootstrap MySQL Router, configure Keepalived
       └── maincontainer: start Keepalived, start MySQL Router

4. Start MySQL Management — Node 1 as BACKUP (Controller.start_mysql_mgmt)
   └── Same as step 3 but with state=BACKUP, priority=90

5. Start Superset (Controller.start_superset)
   └── For each management node:
       ├── Upload services/superset directory and TLS certificates
       ├── Initialize Docker Swarm (first node) and create overlay network
       ├── Start Redis container on overlay network
       └── Create Superset Swarm service with secrets and TLS mounts

6. Cleanup
   └── Close all SSH and SFTP connections
```

## Remote Execution Model

The controller runs on the user's workstation and communicates with cluster nodes over SSH using
[Paramiko](https://www.paramiko.org/). The `RemoteConnection` class provides:

- **SSH/SFTP connections**: connects as the `superset` user, either directly or through `~/.ssh/config`.
- **Python bytecode execution**: `container.py` source is compiled to `.pyc`, uploaded to the remote node, and
  executed via `python3 /opt/<nonce>.pyc`. This allows running Docker API commands on remote nodes without
  installing additional management software.
- **Directory and file uploads**: recursive SFTP-based uploads of service directories, certificates, and passwords.

## Networking

### Host Network Mode

MySQL Server and MySQL Management containers run with `network_mode: host`, sharing the host's network stack.
This enables:

- Direct access to MySQL on port 3306 from other nodes using hostnames.
- Keepalived to manage the VIP directly on the host's network interface.
- MySQL Router to bind to the host's port 6446.

### Docker Swarm Overlay Network

Redis and Superset run on the `superset-network` overlay network, which provides:

- Service discovery: Superset connects to Redis using the hostname `redis`.
- Port publishing: Swarm publishes port 443 on all Swarm nodes via VIP-based routing.

### Port Summary

| Port | Protocol | Service | Scope |
|------|----------|---------|-------|
| 443 | HTTPS | Nginx → Superset | External (via VIP) |
| 3306 | MySQL | MySQL Server | Internal (cluster nodes) |
| 6446 | MySQL | MySQL Router (R/W) | Internal (management nodes → VIP) |
| 6379 | Redis | Redis | Internal (overlay network) |
| 8088 | HTTP | Gunicorn | Internal (localhost only) |

### Data Flow

```text
Client ──HTTPS:443──► VIP (Keepalived)
                        │
                        ▼
                   Nginx (TLS termination)
                        │
                        ▼
                   Gunicorn:8088 (Superset)
                        │
                ┌───────┴───────┐
                ▼               ▼
          MySQL Router      Redis:6379
           (port 6446)     (broker + cache)
                │               ▲
                ▼               │
          InnoDB Cluster    Celery Worker
         (3 MySQL nodes)   (async queries)
```

## High Availability

### Management Node Failover

If the active management node fails:

1. Keepalived detects the loss via VRRP advertisement timeout (1-second interval).
2. The backup node promotes itself to `MASTER` and acquires the VIP.
3. Gratuitous ARP updates network switches to route traffic to the new master.
4. MySQL Router on the new master continues serving client connections.

The `nopreempt` setting prevents the original master from reclaiming the VIP after recovery, which avoids
unnecessary failover oscillation.

### MySQL Primary Failover

If the MySQL primary node fails:

1. InnoDB Cluster Group Replication detects the failure through its consensus protocol.
2. One of the two secondary nodes is automatically elected as the new primary.
3. MySQL Router detects the topology change and redirects read-write traffic to the new primary.
4. The cluster status transitions from `OK` to `OK_NO_TOLERANCE_PARTIAL`, indicating reduced fault tolerance.

### Superset Service Recovery

Superset runs as a Docker Swarm service with `maxreplicas=1`. If the Superset container fails, Docker Swarm
automatically reschedules it on an available manager node. The service connects to MySQL through the VIP (port
6446), so it is transparent to management node failovers.

## Metaclass Pattern

The codebase uses the `Overlay` metaclass (`src/decorators.py`) to control method execution:

- **`@run_all_methods`**: class decorator that invokes all public methods on class definition (used by
  `ArgumentParser` for input validation).
- **`@run_selected_methods_once`**: marks methods to be auto-invoked when the class is instantiated (used by
  `Controller.credentials`).
- **`@single_sign_on`**: ensures a method runs exactly once across all calls, caching the result with thread-safe
  locking.

This pattern enables declarative initialization where creating an instance of `Controller` automatically validates
arguments and generates credentials before `start_cluster()` is called.
