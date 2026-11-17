import json
import os
import time
import redis

r = redis.Redis(
    host=os.environ.get('REDIS_HOST', '127.0.0.1'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=1,
    decode_responses=True,
    socket_connect_timeout=1,
)

# if redis is down we stop trying for 30 seconds so the app does not become slow
down_until = 0


def is_up():
    return time.time() > down_until


def failed():
    global down_until
    down_until = time.time() + 30


# if redis is not running the app should still work, so errors are ignored
def get(key):
    if not is_up():
        return None
    try:
        value = r.get(key)
        if value is not None:
            return json.loads(value)
    except redis.RedisError:
        failed()
    return None


def put(key, data, seconds=60):
    if not is_up():
        return
    try:
        r.setex(key, seconds, json.dumps(data))
    except redis.RedisError:
        failed()


def clear(prefix):
    if not is_up():
        return
    try:
        for key in r.scan_iter(prefix + '*'):
            r.delete(key)
    except redis.RedisError:
        failed()
