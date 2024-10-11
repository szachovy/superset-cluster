"""
temporary
"""
import json
import os

import superset  # pylint: disable=import-error
import superset.models.core  # pylint: disable=import-error


def create_mysql_connection():
    with open(
        file="/run/secrets/mysql_superset_password",
        mode="r",
        encoding="utf-8"
    ) as mysql_superset_password:
        if not superset.db.session.query(superset.models.core.Database).filter_by(database_name='MySQL').first():
            mysql_connection = superset.models.core.Database(
                database_name='MySQL',
                allow_run_async=True,
                sqlalchemy_uri=f"mysql+mysqlconnector://superset:{mysql_superset_password.read().strip()}@{os.environ.get('VIRTUAL_IP_ADDRESS')}:6446/superset",  # noqa: E501 pylint: disable=line-too-long
                extra=json.dumps({
                    "async": True,
                    "engine_params": {},
                    "metadata_params": {},
                    "schemas_allowed_for_csv_upload": []
                })
            )
            superset.db.session.add(mysql_connection)
            superset.db.session.commit()
