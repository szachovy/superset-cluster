#!/usr/bin/env python3
import os
import sys

pw = os.environ["DB_PASSWORD"]
for line in sys.stdin:
    sys.stdout.write(line.replace(pw, "<redacted>"))
    sys.stdout.flush()
