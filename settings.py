ZEPHYR_TO_SLACK = {
    'thetans': '#zephyr',
    }

SLACK_TO_ZEPHYR = {
    'zephyr': 'thetans',
    }

SLACK_URL = None
SLACK_TOKEN = None

PORT = 8123

try:
    from local_settings import *
except ImportError as e:
    pass
