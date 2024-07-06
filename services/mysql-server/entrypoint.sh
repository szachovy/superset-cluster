#!/bin/bash
export MYSQL_ROOT_PASSWORD=mysql
export MYSQL_PASSWORD=mypass

if [ -f /opt/.mylogin.cnf ]; then
  mv /opt/.mylogin.cnf ${MYSQL_USER}
fi

/opt/store_credentials.sh

docker-entrypoint.sh mysqld &

unset MYSQL_ROOT_PASSWORD
unset MYSQL_PASSWORD

tail -f /dev/null
