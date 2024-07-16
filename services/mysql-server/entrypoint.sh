#!/bin/bash

export MYSQL_ROOT_PASSWORD=$(openssl rand -hex 9)

/opt/store_credentials
docker-entrypoint.sh mysqld &

unset MYSQL_ROOT_PASSWORD
tail -f /dev/null
