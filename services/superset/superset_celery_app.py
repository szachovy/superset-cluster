"""
Custom Celery app wrapper for Superset.

Guarantees that superset.sql_lab.SQL_QUERY_MUTATOR is set to the correct
function from the Flask app config before the Celery prefork pool forks
worker processes.

Background: superset.sql_lab captures SQL_QUERY_MUTATOR at module import
time via config["SQL_QUERY_MUTATOR"] (where config = current_app.config).
In some timing scenarios with the prefork pool, this capture can result in
None, causing 'NoneType' object is not callable during async SQL execution.
"""
# Import from the standard Superset celery entrypoint (runs create_app())
from superset.tasks.celery_app import app, flask_app  # noqa: F401

# Explicitly ensure superset.sql_lab has the correct SQL_QUERY_MUTATOR
# before any worker processes are forked.
import superset.sql_lab as _sql_lab  # noqa: E402
_sql_lab.SQL_QUERY_MUTATOR = flask_app.config["SQL_QUERY_MUTATOR"]
