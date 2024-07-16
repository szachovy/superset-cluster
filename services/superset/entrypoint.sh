#!/bin/bash

/usr/bin/run-server.sh &

celery \
  --app superset.tasks.celery_app:app \
  worker \
  --pool prefork \
  --concurrency 4 \
  -O fair
