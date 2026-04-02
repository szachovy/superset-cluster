# Security

This document covers the security architecture, reliability mechanisms, and performance characteristics of
superset-cluster. For the general system architecture, refer to [ARCHITECTURE.md](ARCHITECTURE.md).

## TLS and Encryption

All data in transit is encrypted using TLS. The cluster operates its own Certificate Authority (CA) generated
during initialization.

### Certificate Hierarchy

```text
Superset-Cluster CA (self-signed, RSA 2048-bit, SHA-256, 365-day validity)
├── MySQL Server certificates (one per MySQL node)
│   └── CN = Superset-Cluster-<hostname>
├── MySQL Router certificates (one per management node)
│   └── CN = Superset-Cluster-<hostname>
└── Superset TLS certificates (one per management node)
    └── CN = <virtual-ip-address>
```

Each certificate is generated from a dedicated RSA 2048-bit private key and a Certificate Signing Request (CSR),
then signed by the cluster CA. All certificates use SHA-256 signatures and have a 365-day validity period.
The `crypto.py` module handles all cryptographic operations using the
[cryptography](https://cryptography.io/) library.

### TLS Endpoints

| Connection | TLS Version | Configuration |
|------------|-------------|---------------|
| Client → Nginx | TLSv1.2, TLSv1.3 | `HIGH:!aNULL:!MD5` cipher suites, server certificate signed by cluster CA |
| MySQL Router → MySQL Server | Required | `--server-ssl-mode REQUIRED`, CA-verified |
| Client → MySQL Router | Required | `--client-ssl-mode REQUIRED`, router presents its own certificate |
| MySQL Server (internal) | Required | `require_secure_transport=ON` in `mysql_config.cnf.tpl` |

### HTTP Security Headers

Nginx adds the following headers to every response:

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Forces HTTPS for 1 year |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking via iframes |
| `X-XSS-Protection` | `1; mode=block` | Enables browser XSS filtering |
| `Referrer-Policy` | `no-referrer-when-downgrade` | Controls referrer information leakage |

Server version tokens are hidden (`server_tokens off`).

## Credential Management

All credentials are generated at initialization time and never stored on the user's workstation after deployment.

### MySQL Root Password

- **Generation**: `base64(os.urandom(16))` — 16 random bytes, Base64-encoded.
- **Storage**: `/opt/superset-cluster/mysql-server/mysql_root_password` (chmod 400 after startup).

The password file starts with permissions `444` during container initialization to allow the MySQL
entrypoint to read it. After the server starts (after `HEALTHCHECK_START_PERIOD`), permissions are
tightened to `400` and ownership is transferred to `root:root`, preventing further reads by the `mysql` user.

### MySQL Superset Password

- **Generation**: 12 random lowercase ASCII characters.
- **Storage**: Docker Compose secret (`/run/secrets/mysql_superset_password`).

### Superset Secret Key

- **Generation**: `base64(os.urandom(42))` — 42 random bytes, Base64-encoded.
- **Storage**: Docker Swarm secret (`/run/secrets/superset_secret_key`).

### MySQL Login Paths

- **Generation**: `mysql_config_editor` obfuscated `.mylogin.cnf`.
- **Storage**: `/opt/superset-cluster/mysql-mgmt/.mylogin.cnf` (chmod 600).

### Docker Swarm Secrets

Superset uses Docker Swarm secrets for the secret key and MySQL password. These are mounted as in-memory
files at `/run/secrets/` inside the container and are never written to the container's filesystem layer.

## Container Security

### Seccomp Profile

MySQL Server containers run with a custom seccomp profile (`seccomp.json`) that uses `SCMP_ACT_ALLOW` as the
default action but explicitly blocks the `kill` syscall (`SCMP_ACT_ERRNO`). This prevents processes inside the
container from sending signals to other processes, limiting the impact of a container compromise.

### Linux Capabilities

Containers are granted only the capabilities they require:

| Container | Capability | Reason |
|-----------|-----------|--------|
| MySQL Server | `SYS_NICE` | Allows setting process scheduling priorities for MySQL threads |
| MySQL Management | `NET_ADMIN` | Required by Keepalived for VIP management and VRRP |

### Process Isolation

- MySQL Server runs as the `mysql` user inside the container. The root password file is owned by `root` after
  startup.
- MySQL Management runs the main processes (`mysqlrouter`, `keepalived`) as the `superset` user. Keepalived
  requires `sudo`, granted via a dedicated sudoers entry (`NOPASSWD: /usr/sbin/keepalived`).
- Superset uses `gosu` to drop from root to the `superset` user for both Nginx and the application entrypoint.

### Image Provenance

Container images are pulled from the GitHub Container Registry (`ghcr.io/szachovy/superset-cluster-*`). MySQL
Shell and MySQL Router binaries are downloaded with MD5 checksum verification and GPG signature validation
against the official MySQL developer signing key.

## MySQL User Permissions

The `superset` MySQL user is created with the following grants (from `superset_user.sql.tpl`):

| Privilege | Scope | Purpose |
|-----------|-------|---------|
| `ALL PRIVILEGES` | `superset.*` | Full access to the Superset application database |
| `INSERT` | `mysql_innodb_cluster_metadata.*` | MySQL Router metadata writes |
| `SELECT, EXECUTE` | `mysql_innodb_cluster_metadata.*` | MySQL Router metadata reads |
| `INSERT, UPDATE, DELETE` | `mysql_innodb_cluster_metadata.routers` | Router registration |
| `INSERT, UPDATE, DELETE` | `mysql_innodb_cluster_metadata.v2_routers` | Router v2 registration |
| `SELECT` | `performance_schema.*` | Monitoring and diagnostics |
| `SELECT` | `mysql.user` | User verification |
| `CREATE USER` | `*.*` | MySQL Router bootstrap requirement |

The user is bound to specific IP addresses (the VIP and each management node's IP), limiting connection
sources.

## Network Security

- Only port **443** (HTTPS) is intended to be exposed externally on the management nodes.
- MySQL (port 3306) and MySQL Router (port 6446) communicate over the internal network only.
- Redis (port 6379) is accessible only within the Docker Swarm overlay network (`superset-network`).
- Gunicorn (port 8088) binds to `localhost` only, accessible exclusively through the Nginx reverse proxy.
- IPv6 should be disabled or configured to be non-routable to prevent unintended network exposure.
- DNS resolution between nodes is required for InnoDB Cluster group replication and SSH connectivity.

## Reliability

### Fault Tolerance

The cluster is designed to survive simultaneous failures of one management node and one MySQL node:

| Failure Scenario | Impact | Recovery |
|------------------|--------|----------|
| Management MASTER fails | VIP migrates to BACKUP via VRRP (1–2 second detection) | Automatic |
| MySQL primary fails | InnoDB Cluster elects new primary from secondaries | Automatic |
| Both above simultaneously | VIP migrates + new primary elected; cluster status: `OK_NO_TOLERANCE_PARTIAL` | Automatic |
| Redis container fails | Restart policy: `always`; Celery tasks retry on broker reconnection | Automatic |
| Superset container fails | Docker Swarm reschedules the service (`maxreplicas=1`) | Automatic |

After a MySQL primary failure, the cluster operates at `OK_NO_TOLERANCE_PARTIAL` status, meaning it can still
serve requests but cannot tolerate an additional MySQL node failure without data unavailability.

### Health Monitoring

Each component has built-in health checks:

| Component | Health Check | Interval | Start Period | Retries |
|-----------|-------------|----------|--------------|---------|
| MySQL Server | `mysqladmin ping` | 5s | 90s | 3 |
| MySQL Management | `pgrep mysqlrouter` (1 process) + `pgrep keepalived` (2 processes) | 5s | 25s | 3 |
| Redis | `redis-cli ping` | 10s | 10s | 5 |
| Superset | `curl -f http://localhost:8088/health` | 60s | 60s | 14 |
| Keepalived | VRRP advertisements every 1s + `mysqlrouter` process tracking | 1s | 15s (startup delay) | — |

### VRRP Behavior

- **`nopreempt`**: the original master does not reclaim the VIP after recovery, preventing failover oscillation.
- **`garp_master_delay 2`**: waits 2 seconds before sending gratuitous ARP after becoming master, allowing the
  network to stabilize.
- **`advert_int 1`**: VRRP advertisements are sent every second; the backup detects master failure within
  approximately 3 seconds (3 × advertisement interval).

### Data Durability

- MySQL InnoDB Cluster uses **GTID-based replication** with group replication consensus, ensuring that committed
  transactions are replicated to at least a majority of nodes before acknowledgment.
- The `READ-COMMITTED` isolation level is used, which is compatible with group replication and provides consistent
  reads without gap locking overhead.
- MySQL Server restart policy is set to `always`, ensuring automatic recovery after transient failures.

## Performance

### Celery Asynchronous Query Execution

Superset uses [Celery](https://docs.celeryq.dev/) for asynchronous SQL query execution, offloading long-running
queries from the web server process:

- **Worker pool**: `prefork` with 4 concurrent worker processes.
- **Fair scheduling** (`-O fair`): tasks are distributed to workers as they become available rather than
  pre-assigned, preventing head-of-line blocking.
- **`task_acks_late`**: tasks are acknowledged only after completion, ensuring that if a worker crashes
  mid-execution, the task is re-delivered to another worker.
- **`worker_prefetch_multiplier: 10`**: each worker prefetches up to 10 tasks, balancing throughput with
  responsiveness.
- **Rate limiting**: `sql_lab.get_sql_results` is rate-limited to 100 requests per second.

### Redis Caching

Redis is used as both the Celery broker and the results backend:

- **Query results cache** (`superset_results` key prefix): SQL Lab query results are cached in Redis, allowing
  repeated access without re-executing queries against MySQL.
- **Filter state cache** (`superset_filter_cache` key prefix): dashboard filter states are cached with an
  86,400-second (24-hour) default TTL.
- Redis runs as a single instance on the overlay network. For latency analysis, see the
  [Redis latency measurement](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/)
  documentation.

### MySQL Performance Configuration

The MySQL server is configured for cluster workloads with the following performance-relevant settings:

| Setting | Value | Effect |
|---------|-------|--------|
| `performance_schema` | `ON` | Enables detailed performance instrumentation |
| `transaction_isolation` | `READ-COMMITTED` | Reduces locking overhead compared to `REPEATABLE-READ` |
| `binlog_transaction_dependency_tracking` | `WRITESET` | Enables parallel replication on secondaries |
| `max_connections` | `50` | Limits concurrent connections per MySQL node |
| `max_connect_errors` | `50` | Blocks hosts after 50 failed connection attempts |

For deeper MySQL performance analysis, refer to:

- [MySQL Performance Schema](https://dev.mysql.com/doc/refman/8.4/en/performance-schema.html)
- [InnoDB Monitors](https://dev.mysql.com/doc/refman/8.4/en/innodb-monitors.html)
- [MySQL Examining Server Thread (Process) Information](https://dev.mysql.com/doc/refman/8.4/en/thread-information.html)

### Nginx Tuning

Nginx is configured for the reverse proxy workload:

- **`sendfile on`**: uses kernel-level file transfer for static content.
- **`keepalive_timeout 65`**: maintains persistent connections to reduce TLS handshake overhead.
- **`tcp_nopush on`** and **`tcp_nodelay on`**: optimizes TCP packet transmission.
- **`multi_accept on`**: accepts multiple connections per worker event loop iteration.
- **`client_max_body_size 50M`**: allows large file uploads (e.g., CSV imports).
- **SSL session cache** (`shared:SSL:10m`): caches TLS sessions to avoid repeated full handshakes.

### Monitoring

The following tools and endpoints are available for cluster monitoring and diagnostics:

- **InnoDB Cluster status**: `mysqlsh --execute "dba.getCluster('superset').status()"` reports cluster health,
  topology mode, and per-node status. See
  [Monitoring InnoDB Cluster](https://dev.mysql.com/doc/mysql-shell/8.0/en/monitoring-innodb-cluster.html).
- **Router list**: `mysqlsh --execute "dba.getCluster('superset').listRouters()"` lists registered MySQL Router
  instances. See
  [Registered Routers](https://dev.mysql.com/doc/mysql-shell/8.0/en/registered-routers.html).
- **Superset health**: `curl -f http://localhost:8088/health` returns the Superset health status.
- **Superset StatsD logging**: can be enabled for metrics collection. See
  [Superset StatsD Logging](https://superset.apache.org/docs/configuration/event-logging/#statsd-logging).
- **Celery monitoring**: `celery inspect ping` and `celery inspect stats` provide worker status. See
  [Celery Async Queries](https://superset.apache.org/docs/configuration/async-queries-celery/).
- **Keepalived logs**: available at `/opt/default/mysql_router/log/keepalived.log` on management nodes.
