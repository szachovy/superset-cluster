#!/bin/bash

set -euo pipefail

VIP="${1:?Usage: $0 <virtual-ip-address>}"
SUPERSET_URL="https://${VIP}"
ITERATIONS="${2:-50}"

echo "=== Superset Cluster Benchmark ==="
echo "Target: ${SUPERSET_URL}"
echo "Iterations: ${ITERATIONS}"
echo

echo "--- Login throughput ---"
LOGIN_PAYLOAD='{"username":"superset","password":"cluster","provider":"db","refresh":true}'
START=$(date +%s%N)
for i in $(seq 1 "${ITERATIONS}"); do
    curl --silent --insecure --output /dev/null --write-out "%{http_code} %{time_total}s\n" \
        --url "${SUPERSET_URL}/api/v1/security/login" \
        --header "Content-Type: application/json" \
        --data "${LOGIN_PAYLOAD}"
done
END=$(date +%s%N)
echo "Total: $(( (END - START) / 1000000 ))ms for ${ITERATIONS} requests"
echo

echo "--- Dashboard API latency ---"
TOKEN=$(curl --silent --insecure \
    --url "${SUPERSET_URL}/api/v1/security/login" \
    --header "Content-Type: application/json" \
    --data "${LOGIN_PAYLOAD}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

for endpoint in "/api/v1/dashboard/" "/api/v1/database/" "/api/v1/chart/"; do
    echo -n "${endpoint}: "
    curl --silent --insecure --output /dev/null --write-out "%{time_total}s\n" \
        --url "${SUPERSET_URL}${endpoint}" \
        --header "Authorization: Bearer ${TOKEN}"
done
echo

echo "--- Redis latency (from mgmt node) ---"
ssh superset@node-0 "docker exec redis redis-cli --latency-history --latency-dist -i 1 2>/dev/null | head -5" \
    2>/dev/null || echo "Redis latency check requires SSH access to node-0"
echo
echo "=== Benchmark complete ==="
