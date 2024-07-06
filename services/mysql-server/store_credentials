#!/usr/bin/expect -f

set hostname [lindex $env(HOSTNAME) 0]
set password [lindex $env(MYSQL_ROOT_PASSWORD) 0]

spawn mysql_config_editor set \
  --login-path=$hostname \
  --host=$hostname \
  --user=root \
  --password

expect "Enter password:"
send "$password\r";

expect eof
