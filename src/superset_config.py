import base64
import secrets
import os
from flask_caching.backends.rediscache import RedisCache

SECRET_KEY = 'secret' #base64.b64encode(secrets.token_bytes(42)).decode()

username = "root"
password = "mysql"
host = "172.18.0.2"
port = "6446"
database = "superset"
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
os.environ['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI

class CeleryConfig(object):
    broker_url = "redis://172.18.0.6:6379/0"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
    )
    result_backend = "redis://172.18.0.6:6379/0"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }

CELERY_CONFIG = CeleryConfig

RESULTS_BACKEND = RedisCache(
    host='172.18.0.6', port=6379, key_prefix='superset_results')

FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_cache',
    'CACHE_REDIS_URL': 'redis://172.18.0.6:6379/0'
}
