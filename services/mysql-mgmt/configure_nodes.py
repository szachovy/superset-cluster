# python3 configure_nodes.py 172.18.0.3, 172.18.0.4, 172.18.0.5

# import subprocess
# import mysqlx
# import sys

# MYSQL_ROOT_PASSWORD = "mysql"

# sessions = {}
# for ip in sys.argv[1:]:
#     print(ip)
#     sessions[ip] = mysqlx.get_session({
#         "host": ip,
#         "port": 33060,
#         "user": "root",
#         "password": MYSQL_ROOT_PASSWORD
#     })

#     result = sessions[ip].sql("SELECT @@hostname;").execute().fetch_one()
#     print(result)

#     command = f"mysqlsh --execute \"dba.configureInstance('{ip}:3306',{{password:'{MYSQL_ROOT_PASSWORD}',interactive:false}});\""
#     subprocess.run(command, shell=True)
    #docker exec mysql-mgmt mysqlsh --execute "dba.configureInstance('${ip}:3306',{password:'${MYSQL_ROOT_PASSWORD}',interactive:false});"
    # for row in result.fetch_all():
    #     print(row)

# finally:
#     # Close the session
#     session.close()


# import mysql.connector


# # Connect to the MySQL server running in the Docker container
# connection = mysql.connector.connect(
#     host="172.18.0.3",
#     port="3306",
#     user="root",
#     password="mysql",
# )

# # Execute the SQL query
# cursor = connection.cursor()
# cursor.execute("SELECT @@hostname;")

# # Fetch the result
# result = cursor.fetchone()[0]
# print(result)

# try:
#     cursor.execute(f"CALL dba.configureInstance('{ip}:3306', {{'password':'{MYSQL_ROOT_PASSWORD}', 'interactive': false}});")
#     connection.commit()
#     print("Instance configured successfully.")
# except mysql.connector.Error as err:
#     print(f"Error: {err}")

# # Close the cursor and connection
# cursor.close()
# connection.close()
