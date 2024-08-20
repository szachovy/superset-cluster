
import flask_caching.backends.rediscache
import os

class CeleryConfig(object):
    broker_url = f"redis://{os.environ.get('VIRTUAL_IP_ADDRESS')}:6379/0"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
    )
    result_backend = f"redis://{os.environ.get('VIRTUAL_IP_ADDRESS')}:6379/0"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }

with open('/run/secrets/superset_secret_key', 'r') as superset_secret_key:
    SECRET_KEY = superset_secret_key.read().strip()

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://superset:cluster@{os.environ.get('VIRTUAL_IP_ADDRESS')}:6446/superset"
CELERY_CONFIG = CeleryConfig
RESULTS_BACKEND = flask_caching.backends.rediscache.RedisCache(host=f"{os.environ.get('VIRTUAL_IP_ADDRESS')}", port=6379, key_prefix='superset_results')
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_cache',
    'CACHE_REDIS_URL': f"redis://{os.environ.get('VIRTUAL_IP_ADDRESS')}:6379/0"
}
