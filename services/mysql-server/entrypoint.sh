#!/bin/bash
export MYSQL_ROOT_PASSWORD=asdqwe
docker-entrypoint.sh mysqld &
unset MYSQL_ROOT_PASSWORD
unset MYSQL_PASSWORD
tail -f /dev/null

# export MYSQL_ROOT_PASSWORD=asdqwe
# mysqld &
# unset MYSQL_ROOT_PASSWORD
