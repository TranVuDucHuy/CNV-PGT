import os
from rq import Queue
from redis import Redis
import time


def _redis_connection() -> Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    return Redis(host=host, port=port)


redis_conn = _redis_connection()
runner_queue = Queue("sandbox_queue", connection=redis_conn)
