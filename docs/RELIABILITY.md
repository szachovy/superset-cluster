# Reliability

This document covers the details of highly available architecture of superset-cluster.

## Fault Tolerance

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

## Health Monitoring

Each component has built-in health checks:

| Component | Health Check | Interval | Start Period | Retries |
|-----------|-------------|----------|--------------|---------|
| MySQL Server | `mysqladmin ping` | 5s | 90s | 3 |
| MySQL Management | `pgrep mysqlrouter` (1 process) + `pgrep keepalived` (2 processes) | 5s | 25s | 3 |
| Redis | `redis-cli ping` | 10s | 10s | 5 |
| Superset | `curl -f http://localhost:8088/health` | 60s | 60s | 14 |
| Keepalived | VRRP advertisements every 1s + `mysqlrouter` process tracking | 1s | 15s (startup delay) | — |

## VRRP Behavior

- **`nopreempt`**: the original master does not reclaim the VIP after recovery, preventing failover oscillation.
- **`garp_master_delay 2`**: waits 2 seconds before sending gratuitous ARP after becoming master, allowing the
  network to stabilize.
- **`advert_int 1`**: VRRP advertisements are sent every second; the backup detects master failure within
  approximately 3 seconds (3 × advertisement interval).

## Data Durability

- MySQL InnoDB Cluster uses **GTID-based replication** with group replication consensus, ensuring that committed
  transactions are replicated to at least a majority of nodes before acknowledgment.
- The `READ-COMMITTED` isolation level is used, which is compatible with group replication and provides consistent
  reads without gap locking overhead.
- MySQL Server restart policy is set to `always`, ensuring automatic recovery after transient failures.
