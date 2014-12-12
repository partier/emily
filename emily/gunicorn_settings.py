# coding: latin-1

import os

workers = os.getenv("WEB_CONCURRENCY", 3)
forwarded_allow_ips="*"
