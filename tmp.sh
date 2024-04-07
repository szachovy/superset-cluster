# mysql -h 172.17.0.2 -u root -p
MSQLSHELL
dba.configureInstance() #https://dev.mysql.com/doc/mysql-shell/8.0/en/configuring-production-instances.html
reboot mysql instance
dba.checkInstanceConfiguration() #(check for "status": "ok")

shell.connect('root@172.17.0.2:3306');
var cluster = dba.createCluster('testCluster')
cluster.setupRouterAccount() #https://dev.mysql.com/doc/mysql-shell/8.0/en/configuring-router-user.html
cluster.setupAdminAccount("icadmin")
cluster.status()
# configure also secondary instances

mysqlsh
dba.configureInstance('root@172.18.0.2:3306',{password:'mysql',interactive:false});
dba.configureInstance('root@172.18.0.3:3306',{password:'mysql',interactive:false});
dba.configureInstance('root@172.18.0.4:3306',{password:'mysql',interactive:false});

shell.connect({user: 'root', host: '172.18.0.2', port: 3306, password: 'mysql'});
cluster=dba.createCluster("mycluster");
cluster=dba.getCluster("mycluster");
cluster.addInstance("root@172.18.0.3:3306",{password:'mysql',interactive:false,recoveryMethod:'incremental'});
cluster.addInstance("root@172.18.0.4:3306",{password:'mysql',interactive:false,recoveryMethod:'incremental'});
cluster.status();

mysqlrouter --bootstrap root@172.18.0.2:3306 --directory /tmp/myrouter --conf-use-sockets --account routerfriend --account-create always
mysqlrouter -c /tmp/myrouter/mysqlrouter.conf
# mysql -u root -h 127.0.0.1 -P 6446 -p
# SELECT @@hostname;
# redis-cli
# SCAN 0