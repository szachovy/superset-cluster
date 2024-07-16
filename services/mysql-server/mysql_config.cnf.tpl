[mysqld]
server_id="${SERVER_ID}"
disabled_storage_engines="MyISAM,BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"
performance_schema="ON"
transaction_isolation="READ-COMMITTED"
binlog_transaction_dependency_tracking="WRITESET"
enforce_gtid_consistency="ON"
gtid_mode="ON"
