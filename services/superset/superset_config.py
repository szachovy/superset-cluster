
import flask_caching.backends.rediscache
import os
import secrets

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

# PREVIOUS_SECRET_KEY = 'secret'
SECRET_KEY = os.environ.get('SECRET_KEY') #secrets.token_hex(12)
GLOBAL_ASYNC_QUERIES = True
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://superset:cluster@{os.environ.get('VIRTUAL_IP_ADDRESS')}:6446/superset"
CELERY_CONFIG = CeleryConfig
RESULTS_BACKEND = flask_caching.backends.rediscache.RedisCache(host='redis', port=6379, key_prefix='superset_results')
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_cache',
    'CACHE_REDIS_URL': 'redis://redis:6379/0'
}

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler = RotatingFileHandler('celery.log', maxBytes=10485760, backupCount=5)
# handler.setFormatter(formatter)

# celery_logger = logging.getLogger('celery')
# celery_logger.setLevel(logging.INFO)
# celery_logger.addHandler(handler)


# from typing import Any
# import click
# from flask.cli import FlaskGroup, with_appcontext
# from superset import app
# from superset.cli.lib import normalize_token
# from superset.extensions import db
# @click.group(
#     cls=FlaskGroup,
#     context_settings={"token_normalize_func": normalize_token},
# )
# @with_appcontext
# def superset() -> None:
#     print(app)
#     @app.shell_context_processor
#     def make_shell_context() -> dict[str, Any]:
#         return {"app": app, "db": db}

# superset().make_shell_context()