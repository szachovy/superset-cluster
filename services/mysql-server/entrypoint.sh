#!/bin/bash

export MYSQL_ROOT_PASSWORD=mysql
#$(openssl rand -hex 9)

/home/superset/store_credentials
docker-entrypoint.sh mysqld &

unset MYSQL_ROOT_PASSWORD
tail -f /dev/null
