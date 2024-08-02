from superset import db
import json
import os
from superset.models.core import Database

def create_mysql_connection():
    new_db = Database(
        database_name='my_async_db',
        sqlalchemy_uri=f"mysql+mysqlconnector://superset:cluster@{os.environ.get('VIRTUAL_IP_ADDRESS')}:6446/superset",
        extra=json.dumps({
            "async": True,
            "engine_params": {
                "connect_args": {
                    "timeout": 600
                }
            },
            "metadata_params": {},
            "schemas_allowed_for_csv_upload": ["public"]
        })
    )
    db.session.add(new_db)
    db.session.commit()
