import os

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISTOGO_URL', 'redis:')