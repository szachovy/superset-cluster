#!/bin/bash

set -euo pipefail

NODE="${1:-node-2}"

echo "Running MySQLTuner on ${NODE}..."
ssh superset@"${NODE}" "docker exec mysql bash -c '
    curl -sL https://raw.githubusercontent.com/major/MySQLTuner-perl/master/mysqltuner.pl -o /tmp/mysqltuner.pl
    perl /tmp/mysqltuner.pl --login-path=root
'"
