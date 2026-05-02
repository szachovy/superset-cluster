#!/bin/bash
set -euo pipefail

killall -0 mysqlrouter 2>/dev/null || exit 1
mysqladmin --login-path=superset --port=6446 ping 2>/dev/null || exit 1
docker info > /dev/null 2>&1 || exit 1
docker service inspect superset --format '{{.Spec.Name}}' 2>/dev/null | grep -q superset || exit 1
docker exec redis redis-cli ping 2>/dev/null | grep -q PONG || exit 1

exit 0
