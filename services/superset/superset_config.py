from flask_caching.backends.rediscache import RedisCache

SECRET_KEY = "secret" #base64.b64encode(secrets.token_bytes(42)).decode()
MYSQL_ROOT_PASSWORD="mysql"
redis_ip="redis"
mysql_ip="172.18.0.2"

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://root:{MYSQL_ROOT_PASSWORD}@{mysql_ip}:6446/superset"


class CeleryConfig(object):
    broker_url = f"redis://{redis_ip}:6379/0"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
    )
    result_backend = f"redis://{redis_ip}:6379/0"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }

CELERY_CONFIG = CeleryConfig

RESULTS_BACKEND = RedisCache(
    host=f'{redis_ip}', port=6379, key_prefix='superset_results')

FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_cache',
    'CACHE_REDIS_URL': f'redis://{redis_ip}:6379/0'
}
