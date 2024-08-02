import json
import os

import superset
import superset.models.core

# https://github.com/apache/superset/blob/40520c54d40f887453827ef36a9f5924119ada62/superset-frontend/src/types/Database.ts#L20

def create_mysql_connection():
    mysql_connection = superset.models.core.Database(
        database_name='MySQL',
        allow_run_async=True,
        sqlalchemy_uri=f"mysql+mysqlconnector://superset:cluster@{os.environ.get('VIRTUAL_IP_ADDRESS')}:6446/superset",
        extra=json.dumps({
            "async": True,
            "engine_params": {},
            "metadata_params": {},
            "schemas_allowed_for_csv_upload": []
        })
    )
    superset.db.session.add(mysql_connection)
    superset.db.session.commit()
