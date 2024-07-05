import docker

client = docker.from_env()

password_data = b"mysql"
secret_name = "superset_mysql_root_password"

secret = client.secrets.create(
    name=secret_name,
    data=password_data
)

print(f"Created secret {secret.id}")