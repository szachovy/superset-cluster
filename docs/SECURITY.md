# Security

This document covers the security architecture of superset-cluster.

## TLS and Encryption

All data in transit is encrypted using TLS. The cluster operates its own Certificate Authority (CA) generated
during initialization.

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
| Client → Nginx | TLSv1.2, TLSv1.3 | `HIGH:!aNULL:!MD5` cipher suites |
| MySQL Router → MySQL Server | Required | `--server-ssl-mode REQUIRED`, CA-verified |
| Client → MySQL Router | Required | `--client-ssl-mode REQUIRED` |
| MySQL Server (internal) | Required | `require_secure_transport=ON` |

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

All credentials are generated at initialization time and never stored on the user's workstation after
deployment.

| Credential | Generation | Storage |
|------------|------------|---------|
| MySQL root password | `base64(os.urandom(16))` | Host filesystem (chmod 400 after startup) |
| MySQL superset password | 12 random lowercase ASCII | Docker secret (`/run/secrets/`) |
| Superset secret key | `base64(os.urandom(42))` | Docker Swarm secret (`/run/secrets/`) |
| MySQL login paths | `mysql_config_editor` `.mylogin.cnf` | Host filesystem (chmod 600) |

The MySQL root password file starts with permissions `444` during container initialization, then is
tightened to `400` with `root:root` ownership after the server starts, preventing further reads by the
`mysql` user. Docker Swarm secrets are mounted as in-memory files and never written to the container's
filesystem layer.

## Container Security

### Seccomp Profile

MySQL Server containers run with a custom seccomp profile (`seccomp.json`) that uses `SCMP_ACT_ALLOW` as
the default action but explicitly blocks the `kill` syscall (`SCMP_ACT_ERRNO`), limiting the impact of a
container compromise.

### Linux Capabilities

Containers are granted only the capabilities they require:

| Container | Capability | Reason |
|-----------|-----------|--------|
| MySQL Server | `SYS_NICE` | Process scheduling priorities for MySQL threads |
| MySQL Management | `NET_ADMIN` | Keepalived VIP management and VRRP |

### Process Isolation

- MySQL Server runs as the `mysql` user. The root password file is owned by `root` after startup.
- MySQL Management runs `mysqlrouter` and `keepalived` as the `superset` user. Keepalived requires
  `sudo`, granted via a dedicated sudoers entry (`NOPASSWD: /usr/sbin/keepalived`).
- Superset uses `gosu` to drop from root to the `superset` user for both Nginx and the application
  entrypoint.

### Image Provenance

Container images are pulled from the GitHub Container Registry (`ghcr.io/szachovy/superset-cluster-*`).
MySQL Shell and MySQL Router binaries are downloaded with MD5 checksum verification and GPG signature
validation against the official MySQL developer signing key.

## MySQL User Permissions

The `superset` MySQL user is created with the following grants (from `superset_user.sql.tpl`):

| Privilege | Scope | Purpose |
|-----------|-------|---------|
| `ALL PRIVILEGES` | `superset.*` | Superset application database |
| `INSERT` | `mysql_innodb_cluster_metadata.*` | Router metadata writes |
| `SELECT, EXECUTE` | `mysql_innodb_cluster_metadata.*` | Router metadata reads |
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

## Supply Chain Security

### Code Scanning

[CodeQL](https://codeql.github.com/) runs on every push and weekly via a scheduled workflow, performing static
analysis on all Python source code. Results are reported to the GitHub Security tab under
[Code scanning alerts](https://github.com/szachovy/superset-cluster/security/code-scanning).

### Dependency Management

[Dependabot](https://docs.github.com/en/code-security/dependabot) is configured to monitor and automatically
propose updates for the following ecosystems on a weekly schedule:

| Ecosystem | Directory | Scope |
|-----------|-----------|-------|
| `docker` | `./tests/setup` | Base image updates |
| `pip` | `./tests/testsuite/roles/testing/files` | Python test dependencies |
| `github-actions` | `/` | CI/CD action versions |
| `terraform` | `./tests/setup` | Terraform provider versions |

Dependabot alerts for known vulnerabilities are available in the
[Security tab](https://github.com/szachovy/superset-cluster/security/dependabot).
