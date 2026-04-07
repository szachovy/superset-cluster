# Performance

This document covers the details of superset-cluster's performance.

## Celery Asynchronous Query Execution

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

## Redis Caching

Redis is used as both the Celery broker and the results backend:

- **Query results cache** (`superset_results` key prefix): SQL Lab query results are cached in Redis, allowing
  repeated access without re-executing queries against MySQL.
- **Filter state cache** (`superset_filter_cache` key prefix): dashboard filter states are cached with an
  86,400-second (24-hour) default TTL.
- Redis runs as a single instance on the overlay network. For latency analysis, see the
  [Redis latency measurement](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/)
  documentation.

## MySQL Performance Configuration

The MySQL server is configured for cluster workloads with the following performance-relevant settings:

| Setting | Value | Effect |
|---------|-------|--------|
| `performance_schema` | `ON` | Enables detailed performance instrumentation |
| `transaction_isolation` | `READ-COMMITTED` | Reduces locking overhead compared to `REPEATABLE-READ` |
| `binlog_transaction_dependency_tracking` | `WRITESET` | Enables parallel replication on secondaries |
| `max_connections` | `50` | Limits concurrent connections per MySQL node |
| `max_connect_errors` | `50` | Blocks hosts after 50 failed connection attempts |

## Nginx Tuning

Nginx is configured for the reverse proxy workload:

- **`sendfile on`**: uses kernel-level file transfer for static content.
- **`keepalive_timeout 65`**: maintains persistent connections to reduce TLS handshake overhead.
- **`tcp_nopush on`** and **`tcp_nodelay on`**: optimizes TCP packet transmission.
- **`multi_accept on`**: accepts multiple connections per worker event loop iteration.
- **`client_max_body_size 50M`**: allows large file uploads (e.g., CSV imports).
- **SSL session cache** (`shared:SSL:10m`): caches TLS sessions to avoid repeated full handshakes.

## Monitoring

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
