import flask_caching.backends.rediscache
import os

class CeleryConfig(object):
    broker_url = "redis://redis:6379/0"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
    )
    result_backend = "redis://redis:6379/0"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }

SECRET_KEY = "secret" #base64.b64encode(secrets.token_bytes(42)).decode()
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://superset:cluster@{os.environ.get('VIRTUAL_IP_ADDRESS')}:6446/superset"
CELERY_CONFIG = CeleryConfig
RESULTS_BACKEND = flask_caching.backends.rediscache.RedisCache(host='redis', port=6379, key_prefix='superset_results')
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_cache',
    'CACHE_REDIS_URL': 'redis://redis:6379/0'
}