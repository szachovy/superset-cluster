"""
Superset Configuration Module

Configuration settings for Apache Superset.

Usage:
------
This module is intended to be used as part of a larger Superset application
setup, providing the necessary configurations to integrate Celery for parallel task
management execution with Redis data management within the application.
To use this configuration, ensure that the required Redis server, Gunicorn web server
and MySQL database are properly set up, then import this module in your
Superset application context.
"""

import os

import flask_caching.backends.rediscache  # pylint: disable=import-error


class CeleryConfig:  # pylint: disable=too-few-public-methods
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


with open(file="/run/secrets/superset_secret_key", mode="r", encoding="utf-8") as superset_secret_key:
    SECRET_KEY = superset_secret_key.read().strip()


with open(file="/run/secrets/mysql_superset_password", mode="r", encoding="utf-8") as mysql_superset_password:
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://superset:{mysql_superset_password.read().strip()}@{os.environ.get('VIRTUAL_IP_ADDRESS')}:6446/superset"  # noqa: E501  pylint: disable=line-too-long

CELERY_CONFIG = CeleryConfig  # pylint: disable=invalid-name
RESULTS_BACKEND = flask_caching.backends.rediscache.RedisCache(host="redis", port=6379, key_prefix="superset_results")
FILTER_STATE_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_filter_cache",
    "CACHE_REDIS_URL": "redis://redis:6379/0"
}
