#!/bin/bash

export MYSQL_ROOT_PASSWORD=mysql
export MYSQL_PASSWORD=mypass

if [ -f /opt/.mylogin.cnf ]; then
  export MYSQL_TEST_LOGIN_FILE=/root/.mylogin.cnf
  mv /opt/.mylogin.cnf /root/
fi

/opt/store_credentials

docker-entrypoint.sh mysqld &

unset MYSQL_ROOT_PASSWORD
unset MYSQL_PASSWORD

tail -f /dev/null
