CREATE USER `superset` IDENTIFIED BY `mysql`;
CREATE DATABASE IF NOT EXISTS `superset`;
GRANT ALL PRIVILEGES ON `superset`.* TO `superset`;
GRANT INSERT ON `mysql_innodb_cluster_metadata`.* TO `superset`;
GRANT SELECT ON `performance_schema`.* TO `superset` WITH GRANT OPTION;
GRANT CREATE USER ON *.* TO `superset`;
GRANT SELECT, EXECUTE ON `mysql_innodb_cluster_metadata`.* TO `superset` WITH GRANT OPTION;
GRANT INSERT, UPDATE, DELETE ON `mysql_innodb_cluster_metadata.routers` TO `superset` WITH GRANT OPTION;
GRANT INSERT, UPDATE, DELETE ON `mysql_innodb_cluster_metadata.v2_routers` TO `superset` WITH GRANT OPTION;
GRANT SELECT ON `mysql.user` TO `superset`;
