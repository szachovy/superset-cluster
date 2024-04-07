from sqlalchemy import create_engine, text
username = "root"
password = "mysql"
host = "172.18.0.5"
port = "6446"
database = "superset"
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
# Establish a connection
with engine.connect() as conn:
    # Execute the SHOW DATABASES command
    result = conn.execute(text("SHOW DATABASES"))
    # Fetch and print the databases
    databases = [row[0] for row in result]
    print("Databases:")
    for db in databases:
        print(db)
